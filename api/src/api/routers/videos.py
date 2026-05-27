from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas.video import VideoResponse
from api.services.video_service import get_video_record, save_upload

router = APIRouter()


@router.post('', response_model=VideoResponse)
async def upload_video(file: UploadFile = File(...)) -> VideoResponse:
    return await save_upload(file)


@router.get('/{video_id}', response_model=VideoResponse)
def get_video(video_id: str) -> VideoResponse:
    record = get_video_record(video_id)
    if record is None:
        raise HTTPException(status_code=404, detail='video not found')
    return record
