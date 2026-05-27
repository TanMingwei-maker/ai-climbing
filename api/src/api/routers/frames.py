from fastapi import APIRouter, HTTPException

from api.schemas.video import FrameExtractRequest, FrameExtractResponse
from api.services.frame_service import extract_video_frame

router = APIRouter()


@router.post("/{video_id}/frames/extract", response_model=FrameExtractResponse)
def extract_frame(video_id: str, payload: FrameExtractRequest) -> FrameExtractResponse:
    try:
        return extract_video_frame(video_id, payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
