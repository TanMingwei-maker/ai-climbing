from pydantic import BaseModel


class AnalysisTaskResponse(BaseModel):
    task_id: str
    video_id: str
    status: str
    message: str
    result_json_url: str | None = None
    result_video_url: str | None = None
