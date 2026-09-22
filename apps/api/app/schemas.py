from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SiteCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    bounds: dict[str, Any] | None = None


class SiteRead(SiteCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class CaptureCreate(BaseModel):
    site_id: str
    label: str
    captured_at: datetime


class CaptureRead(CaptureCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    orthomosaic_url: str | None = None


class DetectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    capture_id: str
    class_name: str
    confidence: float = Field(ge=0, le=1)
    bbox: dict[str, float]
    latitude: float
    longitude: float
    timestamp: datetime
    source_image_id: str | None = None
    model_version: str


class ProcessResponse(BaseModel):
    capture_id: str
    status: str
    message: str
