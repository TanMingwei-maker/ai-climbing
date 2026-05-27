from pydantic import BaseModel


class VideoResponse(BaseModel):
    video_id: str
    filename: str
    status: str


class FrameExtractRequest(BaseModel):
    frame_index: int | None = None
    time_sec: float | None = None


class FrameExtractResponse(BaseModel):
    video_id: str
    frame_name: str
    frame_url: str
    width: int
    height: int
    frame_index: int
    status: str
