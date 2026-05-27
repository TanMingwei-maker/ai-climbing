from __future__ import annotations

import cv2

from api.config import FRAME_DIR
from api.schemas.video import FrameExtractRequest, FrameExtractResponse
from api.services.video_service import get_video_source_path


def extract_video_frame(video_id: str, payload: FrameExtractRequest) -> FrameExtractResponse:
    video_path = get_video_source_path(video_id)
    if video_path is None or not video_path.exists():
        raise FileNotFoundError(f"video not found: {video_id}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"unable to open video: {video_path}")

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        if payload.frame_index is not None:
            frame_index = max(0, min(payload.frame_index, max(total_frames - 1, 0)))
        elif payload.time_sec is not None:
            frame_index = max(0, min(int(payload.time_sec * fps), max(total_frames - 1, 0)))
        else:
            frame_index = max(total_frames // 2, 0)

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("failed to read frame from video")
    finally:
        cap.release()

    frame_dir = FRAME_DIR / video_id
    frame_dir.mkdir(parents=True, exist_ok=True)
    frame_name = f"frame_{frame_index:06d}.jpg"
    frame_path = frame_dir / frame_name
    if not cv2.imwrite(str(frame_path), frame):
        raise RuntimeError("failed to write frame image")

    return FrameExtractResponse(
        video_id=video_id,
        frame_name=frame_name,
        frame_url=f"http://127.0.0.1:8000/static/frames/{video_id}/{frame_name}",
        width=width,
        height=height,
        frame_index=frame_index,
        status="frame_ready",
    )
