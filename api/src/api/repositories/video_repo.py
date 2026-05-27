from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from api.repositories.db import get_connection


@dataclass(slots=True)
class VideoRow:
    video_id: str
    filename: str
    stored_path: str
    status: str
    annotation_path: str | None = None
    result_json_path: str | None = None
    result_video_path: str | None = None


def upsert_video(
    *,
    video_id: str,
    filename: str,
    stored_path: Path,
    status: str,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO videos (video_id, filename, stored_path, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                filename = excluded.filename,
                stored_path = excluded.stored_path,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (video_id, filename, str(stored_path), status),
        )


def update_analysis_result(
    *,
    video_id: str,
    status: str,
    annotation_path: Path | None,
    result_json_path: Path,
    result_video_path: Path,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE videos
            SET status = ?,
                annotation_path = ?,
                result_json_path = ?,
                result_video_path = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE video_id = ?
            """,
            (
                status,
                str(annotation_path) if annotation_path else None,
                str(result_json_path),
                str(result_video_path),
                video_id,
            ),
        )


def update_annotation_path(*, video_id: str, annotation_path: Path) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE videos
            SET annotation_path = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE video_id = ?
            """,
            (str(annotation_path), video_id),
        )


def get_video(video_id: str) -> VideoRow | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT video_id, filename, stored_path, status, annotation_path, result_json_path, result_video_path
            FROM videos
            WHERE video_id = ?
            """,
            (video_id,),
        ).fetchone()

    if row is None:
        return None

    return VideoRow(
        video_id=row["video_id"],
        filename=row["filename"],
        stored_path=row["stored_path"],
        status=row["status"],
        annotation_path=row["annotation_path"],
        result_json_path=row["result_json_path"],
        result_video_path=row["result_video_path"],
    )
