from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import mediapipe as mp

from ai_climbing.metrics import angle_degrees, average, midpoint
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

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(
            str(output_video_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )

        frame_metrics: list[FrameMetrics] = []
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
                    self._draw_pose(frame, result.pose_landmarks)
                    self._draw_overlay(frame, metrics)

                writer.write(frame)
        finally:
            cap.release()
            writer.release()

        summary = self._summarize(frame_metrics)
        feedback = evaluate_climbing_form(summary)
        analysis_result = AnalysisResult(
            total_frames=total_frames,
            analyzed_frames=len(frame_metrics),
            summary=summary,
            feedback=feedback,
        )
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
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @staticmethod
    def _xy(landmark) -> tuple[float, float]:
        return (landmark.x, landmark.y)
