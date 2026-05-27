from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ai_climbing.metrics import angle_degrees, average, midpoint
from ai_climbing.move_sequence import (
    ContactSegment,
    Hold,
    LimbSample,
    LimbState,
    MoveEvent,
    build_limb_states,
    detect_move_sequence,
)
from ai_climbing.phase_segmentation import PhaseSegment, segment_climb_phases
from ai_climbing.route_context import (
    RouteContext,
    apply_route_mapping,
    load_route_context,
    match_holds_to_route,
)
from ai_climbing.rules import FeedbackItem, evaluate_climbing_form


@dataclass(slots=True)
class FrameMetrics:
    frame_index: int
    left_elbow_angle: float
    right_elbow_angle: float
    left_knee_angle: float
    right_knee_angle: float
    hip_to_ankle_dx: float
    hand_height_gap: float


@dataclass(slots=True)
class AnalysisResult:
    total_frames: int
    analyzed_frames: int
    summary: dict[str, float]
    feedback: list[FeedbackItem]
    limb_states: list[LimbState]
    holds: list[Hold]
    contacts: list[ContactSegment]
    move_sequence: list[MoveEvent]
    route_move_sequence: list[MoveEvent]
    phase_segments: list[PhaseSegment]
    route_context: RouteContext | None = None


class ClimbingPoseAnalyzer:
    def __init__(self, detection_confidence: float = 0.5, tracking_confidence: float = 0.5) -> None:
        self.mp_pose = mp.solutions.pose
        self.mp_draw = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )

    def analyze_video(
        self,
        input_path: Path,
        output_video_path: Path,
        output_json_path: Path,
        route_context_path: Path | None = None,
    ) -> AnalysisResult:
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise FileNotFoundError(f"无法打开视频文件: {input_path}")

        frame_metrics: list[FrameMetrics] = []
        limb_samples: list[LimbSample] = []
        total_frames = 0

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                total_frames += 1
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = self.pose.process(rgb_frame)

                if result.pose_landmarks:
                    metrics = self._extract_metrics(result.pose_landmarks, total_frames - 1)
                    frame_metrics.append(metrics)
                    limb_samples.extend(self._extract_limb_samples(result.pose_landmarks, total_frames - 1))
        finally:
            cap.release()

        summary = self._summarize(frame_metrics)
        feedback = evaluate_climbing_form(summary)
        limb_states = build_limb_states(limb_samples)
        holds, contacts, move_sequence = detect_move_sequence(limb_states)
        route_context = load_route_context(route_context_path) if route_context_path else None
        if route_context is not None:
            holds = match_holds_to_route(holds, route_context)
        contacts, route_move_sequence = apply_route_mapping(holds, contacts, move_sequence)
        phase_segments = segment_climb_phases(route_move_sequence, contacts, total_frames)
        analysis_result = AnalysisResult(
            total_frames=total_frames,
            analyzed_frames=len(frame_metrics),
            summary=summary,
            feedback=feedback,
            limb_states=limb_states,
            holds=holds,
            contacts=contacts,
            move_sequence=move_sequence,
            route_move_sequence=route_move_sequence,
            phase_segments=phase_segments,
            route_context=route_context,
        )
        self._render_output_video(input_path, output_video_path, analysis_result)
        output_json_path.write_text(self._to_json(analysis_result), encoding="utf-8")
        return analysis_result

    def _extract_metrics(self, pose_landmarks: mp.framework.formats.landmark_pb2.NormalizedLandmarkList, frame_index: int) -> FrameMetrics:
        landmarks = pose_landmarks.landmark
        pose = self.mp_pose.PoseLandmark

        left_shoulder = self._xy(landmarks[pose.LEFT_SHOULDER])
        right_shoulder = self._xy(landmarks[pose.RIGHT_SHOULDER])
        left_elbow = self._xy(landmarks[pose.LEFT_ELBOW])
        right_elbow = self._xy(landmarks[pose.RIGHT_ELBOW])
        left_wrist = self._xy(landmarks[pose.LEFT_WRIST])
        right_wrist = self._xy(landmarks[pose.RIGHT_WRIST])
        left_hip = self._xy(landmarks[pose.LEFT_HIP])
        right_hip = self._xy(landmarks[pose.RIGHT_HIP])
        left_knee = self._xy(landmarks[pose.LEFT_KNEE])
        right_knee = self._xy(landmarks[pose.RIGHT_KNEE])
        left_ankle = self._xy(landmarks[pose.LEFT_ANKLE])
        right_ankle = self._xy(landmarks[pose.RIGHT_ANKLE])

        center_hip = midpoint(left_hip, right_hip)
        center_ankle = midpoint(left_ankle, right_ankle)

        return FrameMetrics(
            frame_index=frame_index,
            left_elbow_angle=angle_degrees(left_shoulder, left_elbow, left_wrist),
            right_elbow_angle=angle_degrees(right_shoulder, right_elbow, right_wrist),
            left_knee_angle=angle_degrees(left_hip, left_knee, left_ankle),
            right_knee_angle=angle_degrees(right_hip, right_knee, right_ankle),
            hip_to_ankle_dx=abs(center_hip[0] - center_ankle[0]),
            hand_height_gap=abs(left_wrist[1] - right_wrist[1]),
        )

    def _extract_limb_samples(
        self,
        pose_landmarks: mp.framework.formats.landmark_pb2.NormalizedLandmarkList,
        frame_index: int,
    ) -> list[LimbSample]:
        landmarks = pose_landmarks.landmark
        pose = self.mp_pose.PoseLandmark

        return [
            LimbSample(
                frame_index=frame_index,
                limb="left_hand",
                x=landmarks[pose.LEFT_WRIST].x,
                y=landmarks[pose.LEFT_WRIST].y,
                visibility=landmarks[pose.LEFT_WRIST].visibility,
            ),
            LimbSample(
                frame_index=frame_index,
                limb="right_hand",
                x=landmarks[pose.RIGHT_WRIST].x,
                y=landmarks[pose.RIGHT_WRIST].y,
                visibility=landmarks[pose.RIGHT_WRIST].visibility,
            ),
            LimbSample(
                frame_index=frame_index,
                limb="left_foot",
                x=landmarks[pose.LEFT_ANKLE].x,
                y=landmarks[pose.LEFT_ANKLE].y,
                visibility=landmarks[pose.LEFT_ANKLE].visibility,
            ),
            LimbSample(
                frame_index=frame_index,
                limb="right_foot",
                x=landmarks[pose.RIGHT_ANKLE].x,
                y=landmarks[pose.RIGHT_ANKLE].y,
                visibility=landmarks[pose.RIGHT_ANKLE].visibility,
            ),
        ]

    def _draw_pose(self, frame, pose_landmarks) -> None:
        self.mp_draw.draw_landmarks(
            frame,
            pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            connection_drawing_spec=self.mp_draw.DrawingSpec(color=(255, 100, 0), thickness=2),
        )

    def _draw_overlay(self, frame, metrics: FrameMetrics) -> None:
        lines = [
            f"肘角均值: {(metrics.left_elbow_angle + metrics.right_elbow_angle) / 2:.1f}",
            f"膝角均值: {(metrics.left_knee_angle + metrics.right_knee_angle) / 2:.1f}",
            f"髋部偏移: {metrics.hip_to_ankle_dx:.3f}",
            f"双手高差: {metrics.hand_height_gap:.3f}",
        ]
        for idx, line in enumerate(lines):
            self._draw_text(
                frame=frame,
                text=line,
                origin=(20, 30 + idx * 30),
                font_scale=0.8,
                color=(255, 255, 255),
                thickness=2,
            )

    def _draw_move_sequence_overlay(
        self,
        frame,
        frame_index: int,
        holds_by_id: dict[str, Hold],
        route_context: RouteContext | None,
        active_hold_by_limb: dict[str, str],
        recent_events: list[MoveEvent],
    ) -> None:
        if route_context and route_context.holds:
            active_route_holds = self._active_route_holds(active_hold_by_limb, holds_by_id)
            for hold in holds_by_id.values():
                self._draw_detected_hold_overlay(
                    frame,
                    hold,
                    self._active_limb_for_hold(hold.hold_id, active_hold_by_limb),
                )
            for route_hold in route_context.holds:
                center = self._frame_point(frame, route_hold.x, route_hold.y)
                color = (170, 170, 170)
                radius = 10
                is_active = False
                for limb, route_hold_id in active_route_holds.items():
                    if route_hold_id == route_hold.hold_id:
                        color = self._limb_color(limb)
                        radius = 15
                        is_active = True
                        break
                self._draw_hold_marker(frame, center, route_hold.hold_id, color, radius, is_active=is_active)
        else:
            for hold in holds_by_id.values():
                center = self._detected_hold_frame_point(frame, hold)
                color = (170, 170, 170)
                radius = 10
                is_active = False
                for limb, hold_id in active_hold_by_limb.items():
                    if hold_id == hold.hold_id:
                        color = self._limb_color(limb)
                        radius = 15
                        is_active = True
                        break
                self._draw_hold_marker(frame, center, self._hold_display_label(hold), color, radius, is_active=is_active)

        status_lines = ["当前附着", f"帧: {frame_index}"]
        for limb in ("left_hand", "right_hand", "left_foot", "right_foot"):
            hold_id = active_hold_by_limb.get(limb, "-")
            hold_label = hold_id
            if hold_id in holds_by_id:
                hold_label = self._hold_display_label(holds_by_id[hold_id])
            status_lines.append(f"{self._limb_label(limb)}: {hold_label}")

        for idx, line in enumerate(status_lines):
            self._draw_text(
                frame=frame,
                text=line,
                origin=(20, 170 + idx * 24),
                font_scale=0.5 if idx == 0 else 0.55,
                color=(240, 240, 240),
                thickness=2,
            )

        for idx, event in enumerate(recent_events[-3:]):
            hold_label = self._event_display_label(event)
            line = f"{self._limb_label(event.limb)} -> {hold_label}"
            self._draw_text(
                frame=frame,
                text=line,
                origin=(20, 300 + idx * 24),
                font_scale=0.55,
                color=self._limb_color(event.limb),
                thickness=2,
            )

    def _draw_active_limb_guides(
        self,
        frame,
        pose_landmarks: mp.framework.formats.landmark_pb2.NormalizedLandmarkList,
        holds_by_id: dict[str, Hold],
        active_hold_by_limb: dict[str, str],
        limb_states_by_limb: dict[str, LimbState],
        highlighted_limbs: set[str],
    ) -> None:
        limb_points = self._limb_points(frame, pose_landmarks, visibility_threshold=0.5)
        for limb, hold_id in active_hold_by_limb.items():
            limb_sample = limb_points.get(limb)
            hold = holds_by_id.get(hold_id)
            if limb_sample is None or hold is None:
                continue

            limb_point, visibility = limb_sample
            hold_point = self._detected_hold_frame_point(frame, hold)
            state = limb_states_by_limb.get(limb)
            base_color = self._limb_color(limb)
            is_recent = limb in highlighted_limbs
            is_moving = state is not None and state.state == "moving"
            is_low_visibility = visibility < 0.75
            if is_low_visibility:
                line_color = (0, 140, 255)
            elif is_recent:
                line_color = base_color
            else:
                line_color = self._blend_color(base_color, (170, 170, 170), 0.45)
            outline_color = (255, 255, 255) if is_recent else (215, 215, 215)
            outer_thickness = 7 if is_recent else 4
            inner_thickness = 4 if is_recent else 2
            if is_moving:
                self._draw_dashed_line(frame, limb_point, hold_point, outline_color, outer_thickness, dash_length=14)
                self._draw_dashed_line(frame, limb_point, hold_point, line_color, inner_thickness, dash_length=12)
            else:
                cv2.line(frame, limb_point, hold_point, outline_color, outer_thickness, cv2.LINE_AA)
                cv2.line(frame, limb_point, hold_point, line_color, inner_thickness, cv2.LINE_AA)
            if is_recent:
                cv2.circle(frame, limb_point, 10, (255, 255, 255), 2)
            cv2.circle(frame, limb_point, 7, outline_color, -1)
            cv2.circle(frame, limb_point, 4, line_color, -1)
            mid_x = int((limb_point[0] + hold_point[0]) / 2)
            mid_y = int((limb_point[1] + hold_point[1]) / 2)
            label = self._guide_status_label(limb, is_recent=is_recent, is_moving=is_moving, is_low_visibility=is_low_visibility)
            self._draw_label_chip(
                frame=frame,
                text=label,
                origin=self._hold_label_origin(frame, (mid_x, mid_y), label),
                color=line_color,
                font_scale=0.45,
            )

    def _draw_feedback_overlay(self, frame, feedback: list[FeedbackItem]) -> None:
        if not feedback:
            return

        height = frame.shape[0]
        lines = ["动作建议"]
        for item in feedback[:2]:
            lines.append(f"- {item.title}")
        if len(feedback) > 2:
            lines.append(f"+ 另外 {len(feedback) - 2} 条")

        start_y = max(30, height - 72)
        for idx, line in enumerate(lines):
            self._draw_text(
                frame=frame,
                text=line,
                origin=(20, start_y + idx * 22),
                font_scale=0.55,
                color=(255, 230, 170),
                thickness=2,
            )

    def _render_output_video(self, input_path: Path, output_video_path: Path, result: AnalysisResult) -> None:
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise FileNotFoundError(f"无法重新读取视频文件: {input_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(
            str(output_video_path),
            cv2.VideoWriter_fourcc(*"avc1"),
            fps,
            (width, height),
        )

        holds_by_id = {hold.hold_id: hold for hold in result.holds}
        events_by_frame: dict[int, list[MoveEvent]] = {}
        for event in result.route_move_sequence:
            events_by_frame.setdefault(event.frame_index, []).append(event)
        limb_states_by_frame: dict[int, dict[str, LimbState]] = {}
        for state in result.limb_states:
            limb_states_by_frame.setdefault(state.frame_index, {})[state.limb] = state

        active_hold_by_limb: dict[str, str] = {}
        recent_events: list[MoveEvent] = []
        highlighted_until_by_limb: dict[str, int] = {}
        frame_index = 0

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pose_result = self.pose.process(rgb_frame)
                if pose_result.pose_landmarks:
                    metrics = self._extract_metrics(pose_result.pose_landmarks, frame_index)
                    self._draw_pose(frame, pose_result.pose_landmarks)
                    self._draw_overlay(frame, metrics)

                for event in events_by_frame.get(frame_index, []):
                    active_hold_by_limb[event.limb] = event.hold_id
                    recent_events.append(event)
                    highlighted_until_by_limb[event.limb] = frame_index + 18

                recent_events = [event for event in recent_events if frame_index - event.frame_index <= 20]
                if pose_result.pose_landmarks:
                    highlighted_limbs = {
                        limb for limb, end_frame in highlighted_until_by_limb.items() if frame_index <= end_frame
                    }
                    self._draw_active_limb_guides(
                        frame,
                        pose_result.pose_landmarks,
                        holds_by_id,
                        active_hold_by_limb,
                        limb_states_by_frame.get(frame_index, {}),
                        highlighted_limbs,
                    )
                self._draw_move_sequence_overlay(
                    frame,
                    frame_index,
                    holds_by_id,
                    result.route_context,
                    active_hold_by_limb,
                    recent_events,
                )
                self._draw_phase_overlay(frame, frame_index, result.phase_segments, result.total_frames)
                if result.route_context:
                    self._draw_route_context_overlay(frame, result.route_context, result.holds)
                self._draw_feedback_overlay(frame, result.feedback)
                writer.write(frame)
                frame_index += 1
        finally:
            cap.release()
            writer.release()

    def _summarize(self, frame_metrics: list[FrameMetrics]) -> dict[str, float]:
        return {
            "avg_elbow_angle": average(
                (m.left_elbow_angle + m.right_elbow_angle) / 2.0 for m in frame_metrics
            ),
            "avg_knee_angle": average(
                (m.left_knee_angle + m.right_knee_angle) / 2.0 for m in frame_metrics
            ),
            "avg_hip_to_ankle_dx": average(m.hip_to_ankle_dx for m in frame_metrics),
            "avg_hand_height_gap": average(m.hand_height_gap for m in frame_metrics),
        }

    def _to_json(self, result: AnalysisResult) -> str:
        payload = {
            "total_frames": result.total_frames,
            "analyzed_frames": result.analyzed_frames,
            "summary": result.summary,
            "feedback": [asdict(item) for item in result.feedback],
            "route_context": asdict(result.route_context) if result.route_context else None,
            "holds": [asdict(item) for item in result.holds],
            "contacts": [asdict(item) for item in result.contacts],
            "move_sequence": [asdict(item) for item in result.move_sequence],
            "route_move_sequence": [asdict(item) for item in result.route_move_sequence],
            "phase_segments": [asdict(item) for item in result.phase_segments],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @staticmethod
    def _xy(landmark) -> tuple[float, float]:
        return (landmark.x, landmark.y)

    def _limb_points(
        self,
        frame,
        pose_landmarks: mp.framework.formats.landmark_pb2.NormalizedLandmarkList,
        visibility_threshold: float,
    ) -> dict[str, tuple[tuple[int, int], float]]:
        landmarks = pose_landmarks.landmark
        pose = self.mp_pose.PoseLandmark
        mapping = {
            "left_hand": landmarks[pose.LEFT_WRIST],
            "right_hand": landmarks[pose.RIGHT_WRIST],
            "left_foot": landmarks[pose.LEFT_ANKLE],
            "right_foot": landmarks[pose.RIGHT_ANKLE],
        }
        points: dict[str, tuple[tuple[int, int], float]] = {}
        for limb, landmark in mapping.items():
            if landmark.visibility < visibility_threshold:
                continue
            points[limb] = (self._frame_point(frame, landmark.x, landmark.y), landmark.visibility)
        return points

    @staticmethod
    def _limb_label(limb: str) -> str:
        labels = {
            "left_hand": "LH",
            "right_hand": "RH",
            "left_foot": "LF",
            "right_foot": "RF",
        }
        return labels.get(limb, limb)

    @staticmethod
    def _limb_color(limb: str) -> tuple[int, int, int]:
        colors = {
            "left_hand": (0, 220, 255),
            "right_hand": (255, 220, 0),
            "left_foot": (0, 180, 0),
            "right_foot": (255, 0, 180),
        }
        return colors.get(limb, (200, 200, 200))

    @staticmethod
    def _frame_point(frame, x: float, y: float) -> tuple[int, int]:
        height, width = frame.shape[:2]
        px = max(0, min(width - 1, int(x * width)))
        py = max(0, min(height - 1, int(y * height)))
        return (px, py)

    def _detected_hold_frame_point(self, frame, hold: Hold) -> tuple[int, int]:
        x = hold.x
        y = hold.y
        return self._frame_point(frame, x, y)

    @staticmethod
    def _active_route_holds(active_hold_by_limb: dict[str, str], holds_by_id: dict[str, Hold]) -> dict[str, str]:
        active_route_holds: dict[str, str] = {}
        for limb, hold_id in active_hold_by_limb.items():
            hold = holds_by_id.get(hold_id)
            if hold is None:
                continue
            active_route_holds[limb] = hold.route_hold_id or hold.hold_id
        return active_route_holds

    @staticmethod
    def _active_limb_for_hold(hold_id: str, active_hold_by_limb: dict[str, str]) -> str | None:
        for limb, active_hold_id in active_hold_by_limb.items():
            if active_hold_id == hold_id:
                return limb
        return None

    @staticmethod
    def _hold_display_label(hold: Hold) -> str:
        return hold.route_hold_id or hold.hold_id.replace("hold_", "H")

    @staticmethod
    def _event_display_label(event: MoveEvent) -> str:
        return event.sequence_hold_id or event.route_hold_id or event.hold_id.replace("hold_", "H")

    def _guide_status_label(
        self,
        limb: str,
        *,
        is_recent: bool,
        is_moving: bool,
        is_low_visibility: bool,
    ) -> str:
        suffix = ""
        if is_recent:
            suffix = "新变化"
        elif is_moving:
            suffix = "移动中"
        elif is_low_visibility:
            suffix = "低可见"
        return f"{self._limb_label(limb)} {suffix}".strip()

    def _draw_route_context_overlay(self, frame, route_context: RouteContext, holds: list[Hold]) -> None:
        matched_count = sum(1 for hold in holds if hold.route_hold_id)
        title = route_context.route_name or "Route"
        wall_text = route_context.wall_name or "Wall"
        angle_text = f"{route_context.wall_angle_deg:.0f}deg" if route_context.wall_angle_deg is not None else "unknown"
        self._draw_text(
            frame=frame,
            text=f"路线: {title} | 墙面: {wall_text} | 角度: {angle_text}",
            origin=(20, 390),
            font_scale=0.55,
            color=(220, 220, 220),
            thickness=2,
        )
        self._draw_text(
            frame=frame,
            text=f"路线匹配: {matched_count}/{len(holds)}",
            origin=(20, 414),
            font_scale=0.55,
            color=(220, 220, 220),
            thickness=2,
        )
        self._draw_text(
            frame=frame,
            text="空心点=人工标注 | 实心点=识别点 | 连线=融合匹配",
            origin=(20, 438),
            font_scale=0.48,
            color=(200, 200, 200),
            thickness=2,
        )

    def _draw_phase_overlay(
        self,
        frame,
        frame_index: int,
        phase_segments: list[PhaseSegment],
        total_frames: int,
    ) -> None:
        active_phase = None
        for phase in phase_segments:
            if phase.start_frame <= frame_index <= phase.end_frame:
                active_phase = phase
                break
        if active_phase is None and phase_segments:
            active_phase = phase_segments[-1]
        if active_phase is None:
            return

        phase_label = self._phase_type_label(active_phase.phase_type)
        progress_start = int((active_phase.start_frame / max(total_frames, 1)) * 100)
        progress_end = int((active_phase.end_frame / max(total_frames, 1)) * 100)
        lines = [
            f"阶段: {phase_label}",
            f"区间: {active_phase.start_frame}-{active_phase.end_frame} 帧 ({progress_start}% - {progress_end}%)",
            f"事件: {active_phase.event_count} | 点位: {', '.join(active_phase.holds[:3]) or '-'}",
        ]
        for idx, line in enumerate(lines):
            self._draw_text(
                frame=frame,
                text=line,
                origin=(20, 450 + idx * 24),
                font_scale=0.52 if idx else 0.6,
                color=(200, 255, 200),
                thickness=2,
            )

    @staticmethod
    def _phase_type_label(phase_type: str) -> str:
        labels = {
            "start": "起步段",
            "transition": "过渡段",
            "finish": "结束段",
        }
        return labels.get(phase_type, phase_type)

    def _draw_hold_marker(
        self,
        frame,
        center: tuple[int, int],
        label: str,
        color: tuple[int, int, int],
        radius: int,
        *,
        is_active: bool,
    ) -> None:
        halo_color = (255, 255, 255)
        cv2.circle(frame, center, radius + 4, halo_color, 3)
        cv2.circle(frame, center, radius, color, 3)
        cv2.circle(frame, center, max(3, radius // 3), color, -1)

        if is_active:
            cv2.circle(frame, center, radius + 9, color, 2)
            cv2.line(frame, (center[0] - radius - 4, center[1]), (center[0] + radius + 4, center[1]), color, 2)
            cv2.line(frame, (center[0], center[1] - radius - 4), (center[0], center[1] + radius + 4), color, 2)

        label_origin = self._hold_label_origin(frame, center, label)
        self._draw_label_chip(
            frame=frame,
            text=label,
            origin=label_origin,
            color=color,
            font_scale=0.55,
        )

    def _draw_detected_hold_overlay(
        self,
        frame,
        hold: Hold,
        active_limb: str | None,
    ) -> None:
        detected_center = self._detected_hold_frame_point(frame, hold)
        detected_color = self._limb_color(active_limb) if active_limb else (130, 210, 255)
        if hold.route_x is not None and hold.route_y is not None:
            route_center = self._frame_point(frame, hold.route_x, hold.route_y)
            distance = hold.match_distance or math.hypot(hold.x - hold.route_x, hold.y - hold.route_y)
            line_color = (80, 220, 120) if distance <= 0.05 else (0, 170, 255)
            cv2.line(frame, detected_center, route_center, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.line(frame, detected_center, route_center, line_color, 1, cv2.LINE_AA)
        cv2.circle(frame, detected_center, 6 if active_limb else 5, (255, 255, 255), 2)
        cv2.circle(frame, detected_center, 4 if active_limb else 3, detected_color, -1)
        if active_limb:
            label = f"{self._limb_label(active_limb)} 识别"
            self._draw_label_chip(
                frame=frame,
                text=label,
                origin=self._hold_label_origin(frame, detected_center, label),
                color=detected_color,
                font_scale=0.42,
            )

    def _draw_label_chip(
        self,
        frame,
        text: str,
        origin: tuple[int, int],
        color: tuple[int, int, int],
        font_scale: float,
    ) -> None:
        x, y = origin
        (text_width, text_height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
        top_left = (x - 6, y - text_height - 6)
        bottom_right = (x + text_width + 6, y + baseline + 4)
        cv2.rectangle(frame, top_left, bottom_right, (20, 20, 20), -1)
        cv2.rectangle(frame, top_left, bottom_right, color, 2)
        self._draw_text(
            frame=frame,
            text=text,
            origin=(x, y),
            font_scale=font_scale,
            color=(255, 255, 255),
            thickness=2,
        )

    @staticmethod
    def _hold_label_origin(frame, center: tuple[int, int], label: str) -> tuple[int, int]:
        height, width = frame.shape[:2]
        text_width, text_height = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)[0]
        x = min(max(12, center[0] + 14), max(12, width - text_width - 16))
        preferred_y = center[1] - 14
        fallback_y = min(height - 12, center[1] + text_height + 14)
        y = preferred_y if preferred_y >= text_height + 12 else fallback_y
        return (x, y)

    @staticmethod
    def _blend_color(
        primary: tuple[int, int, int],
        secondary: tuple[int, int, int],
        ratio: float,
    ) -> tuple[int, int, int]:
        clamped_ratio = max(0.0, min(1.0, ratio))
        return tuple(
            int(primary[idx] * (1.0 - clamped_ratio) + secondary[idx] * clamped_ratio)
            for idx in range(3)
        )

    @staticmethod
    def _draw_dashed_line(
        frame,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int],
        thickness: int,
        dash_length: int,
    ) -> None:
        distance = int(np.hypot(end[0] - start[0], end[1] - start[1]))
        if distance == 0:
            return
        for offset in range(0, distance, dash_length * 2):
            start_ratio = offset / distance
            end_ratio = min(offset + dash_length, distance) / distance
            x1 = int(start[0] + (end[0] - start[0]) * start_ratio)
            y1 = int(start[1] + (end[1] - start[1]) * start_ratio)
            x2 = int(start[0] + (end[0] - start[0]) * end_ratio)
            y2 = int(start[1] + (end[1] - start[1]) * end_ratio)
            cv2.line(frame, (x1, y1), (x2, y2), color, thickness, cv2.LINE_AA)

    def _draw_text(
        self,
        frame,
        text: str,
        origin: tuple[int, int],
        font_scale: float,
        color: tuple[int, int, int],
        thickness: int,
    ) -> None:
        x, y = origin
        if text.isascii():
            cv2.putText(
                frame,
                text,
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                color,
                thickness,
                cv2.LINE_AA,
            )
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)
        draw = ImageDraw.Draw(image)
        font = self._overlay_font(max(14, int(26 * font_scale)))
        draw.text((x, max(0, y - font.size)), text, font=font, fill=(color[2], color[1], color[0]))
        frame[:] = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    @staticmethod
    @lru_cache(maxsize=8)
    def _overlay_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        candidates = (
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        )
        for path in candidates:
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
        return ImageFont.load_default()
