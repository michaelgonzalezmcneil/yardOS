from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class Center(BaseModel):
    x: float
    y: float


class DetectionResponseItem(BaseModel):
    class_name: str = Field(serialization_alias="class")
    confidence: float = Field(ge=0, le=1)
    bbox: BoundingBox
    center: Center


class DetectionResponse(BaseModel):
    detections: list[DetectionResponseItem]
    image_width: int
    image_height: int
    model_version: str
    inference_time_ms: float
    tiled: bool


class HealthResponse(BaseModel):
    status: str
    provider: str
    model_version: str
