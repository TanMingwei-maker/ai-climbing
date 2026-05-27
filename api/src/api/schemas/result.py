from pydantic import BaseModel


class AnalysisResultResponse(BaseModel):
    video_id: str
    status: str
    result_json_url: str
    result_video_url: str
