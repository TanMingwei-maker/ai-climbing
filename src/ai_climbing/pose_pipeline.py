from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import mediapipe as mp

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

    def analyze_video(self, input_path: Path, output_video_path: Path, output_json_path: Path) -> AnalysisResult:
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
        analysis_result = AnalysisResult(
            total_frames=total_frames,
            analyzed_frames=len(frame_metrics),
            summary=summary,
            feedback=feedback,
            limb_states=limb_states,
            holds=holds,
            contacts=contacts,
            move_sequence=move_sequence,
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
            f"Elbow avg: {(metrics.left_elbow_angle + metrics.right_elbow_angle) / 2:.1f}",
            f"Knee avg: {(metrics.left_knee_angle + metrics.right_knee_angle) / 2:.1f}",
            f"Hip shift: {metrics.hip_to_ankle_dx:.3f}",
        ]
        for idx, line in enumerate(lines):
            cv2.putText(
                frame,
                line,
                (20, 30 + idx * 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

    def _draw_move_sequence_overlay(
        self,
        frame,
        frame_index: int,
        holds_by_id: dict[str, Hold],
        active_hold_by_limb: dict[str, str],
        recent_events: list[MoveEvent],
    ) -> None:
        for hold in holds_by_id.values():
            center = self._frame_point(frame, hold.x, hold.y)
            color = (90, 90, 90)
            radius = 8
            for limb, hold_id in active_hold_by_limb.items():
                if hold_id == hold.hold_id:
                    color = self._limb_color(limb)
                    radius = 12
                    break
            cv2.circle(frame, center, radius, color, 2)
            cv2.putText(
                frame,
                hold.hold_id.replace("hold_", "H"),
                (center[0] + 8, center[1] - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1,
                cv2.LINE_AA,
            )

        status_lines = [f"Frame: {frame_index}"]
        for limb in ("left_hand", "right_hand", "left_foot", "right_foot"):
            hold_id = active_hold_by_limb.get(limb, "-")
            status_lines.append(f"{self._limb_label(limb)}: {hold_id}")

        for idx, line in enumerate(status_lines):
            cv2.putText(
                frame,
                line,
                (20, 140 + idx * 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (240, 240, 240),
                2,
                cv2.LINE_AA,
            )

        for idx, event in enumerate(recent_events[-3:]):
            line = f"{self._limb_label(event.limb)} -> {event.hold_id}"
            cv2.putText(
                frame,
                line,
                (20, 270 + idx * 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                self._limb_color(event.limb),
                2,
                cv2.LINE_AA,
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
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )

        holds_by_id = {hold.hold_id: hold for hold in result.holds}
        events_by_frame: dict[int, list[MoveEvent]] = {}
        for event in result.move_sequence:
            events_by_frame.setdefault(event.frame_index, []).append(event)

        active_hold_by_limb: dict[str, str] = {}
        recent_events: list[MoveEvent] = []
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

                recent_events = [event for event in recent_events if frame_index - event.frame_index <= 20]
                self._draw_move_sequence_overlay(frame, frame_index, holds_by_id, active_hold_by_limb, recent_events)
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
            "holds": [asdict(item) for item in result.holds],
            "contacts": [asdict(item) for item in result.contacts],
            "move_sequence": [asdict(item) for item in result.move_sequence],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @staticmethod
    def _xy(landmark) -> tuple[float, float]:
        return (landmark.x, landmark.y)

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
