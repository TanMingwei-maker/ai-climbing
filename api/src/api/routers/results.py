from fastapi import APIRouter, HTTPException

from api.schemas.result import AnalysisResultResponse
from api.services.analysis_service import get_analysis_result

router = APIRouter()


@router.get("/{video_id}/result", response_model=AnalysisResultResponse)
def get_result(video_id: str) -> AnalysisResultResponse:
    try:
        return get_analysis_result(video_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
