from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from api.config import UPLOAD_DIR
from api.repositories.video_repo import get_video, upsert_video
from api.schemas.video import VideoResponse


@dataclass(slots=True)
class StoredVideoRecord:
    video_id: str
    filename: str
    stored_path: Path
    status: str = "uploaded"

    def to_response(self) -> VideoResponse:
        return VideoResponse(video_id=self.video_id, filename=self.filename, status=self.status)

async def save_upload(file: UploadFile) -> VideoResponse:
    video_id = f"vid_{uuid.uuid4().hex[:8]}"
    filename = file.filename or f"{video_id}.mp4"
    suffix = Path(filename).suffix or ".mp4"
    target = UPLOAD_DIR / f"{video_id}{suffix}"
    content = await file.read()
    target.write_bytes(content)
    record = StoredVideoRecord(video_id=video_id, filename=filename, stored_path=target)
    upsert_video(video_id=video_id, filename=filename, stored_path=target, status=record.status)
    return record.to_response()


def get_video_record(video_id: str) -> VideoResponse | None:
    record = get_video(video_id)
    if record is None:
        return None
    return VideoResponse(video_id=record.video_id, filename=record.filename, status=record.status)


def get_video_source_path(video_id: str) -> Path | None:
    record = get_video(video_id)
    if record is None:
        return None
    return Path(record.stored_path)
