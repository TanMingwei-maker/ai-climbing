from fastapi import APIRouter, HTTPException

from api.schemas.task import AnalysisTaskResponse
from api.services.analysis_service import create_analysis_task

router = APIRouter()


@router.post('/{video_id}/analyze', response_model=AnalysisTaskResponse)
def analyze_video(video_id: str) -> AnalysisTaskResponse:
    try:
        return create_analysis_task(video_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
