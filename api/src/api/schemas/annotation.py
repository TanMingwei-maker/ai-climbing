from pydantic import BaseModel, Field


class WallPayload(BaseModel):
    name: str | None = None
    angle_deg: float | None = None


class RoutePayload(BaseModel):
    name: str | None = None


class RouteHoldPayload(BaseModel):
    id: str
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    role: str | None = None


class RouteContextPayload(BaseModel):
    wall: WallPayload = Field(default_factory=WallPayload)
    route: RoutePayload = Field(default_factory=RoutePayload)
    holds: list[RouteHoldPayload] = Field(default_factory=list)
