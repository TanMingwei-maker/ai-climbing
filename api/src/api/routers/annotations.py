from fastapi import APIRouter

from api.schemas.annotation import RouteContextPayload
from api.services.annotation_service import load_route_context, save_route_context

router = APIRouter()


@router.get('/{video_id}/route-context', response_model=RouteContextPayload)
def get_route_context(video_id: str) -> RouteContextPayload:
    return load_route_context(video_id)


@router.put('/{video_id}/route-context', response_model=RouteContextPayload)
def put_route_context(video_id: str, payload: RouteContextPayload) -> RouteContextPayload:
    return save_route_context(video_id, payload)
