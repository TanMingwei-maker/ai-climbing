from pathlib import Path

from api.config import ANNOTATION_DIR
from api.repositories.video_repo import update_annotation_path
from api.schemas.annotation import RouteContextPayload


def _annotation_path(video_id: str) -> Path:
    return ANNOTATION_DIR / f'{video_id}.route_context.json'


def load_route_context(video_id: str) -> RouteContextPayload:
    path = _annotation_path(video_id)
    if not path.exists():
        return RouteContextPayload()
    return RouteContextPayload.model_validate_json(path.read_text(encoding='utf-8'))


def save_route_context(video_id: str, payload: RouteContextPayload) -> RouteContextPayload:
    path = _annotation_path(video_id)
    path.write_text(payload.model_dump_json(indent=2), encoding='utf-8')
    update_annotation_path(video_id=video_id, annotation_path=path)
    return payload
