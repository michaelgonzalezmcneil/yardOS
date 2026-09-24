from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import NAMESPACE_URL, uuid4, uuid5

GeoJSON = dict[str, Any]


def new_id() -> str:
    return str(uuid4())


def stable_id(kind: str, *parts: object) -> str:
    """Deterministic ID for idempotent provider and pipeline output."""
    return str(uuid5(NAMESPACE_URL, "yardos:" + kind + ":" + ":".join(str(part) for part in parts)))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ArtifactType(StrEnum):
    RAW_IMAGE = "raw_image"
    RAW_VIDEO = "raw_video"
    ORTHOMOSAIC = "orthomosaic"
    DEM = "dem"
    POINT_CLOUD = "point_cloud"
    TILE = "tile"
    SEGMENTATION_MASK = "segmentation_mask"
    CHANGE_MASK = "change_mask"
    THUMBNAIL = "thumbnail"
    METADATA = "metadata"


class ProcessingState(StrEnum):
    PENDING = "pending"
    # Backwards-compatible name for API callers created before the canonical
    # job vocabulary was finalized.
    QUEUED = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class Site:
    name: str
    boundary_geo: GeoJSON | None = None
    id: str = field(default_factory=new_id)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class Capture:
    site_id: str
    label: str
    id: str = field(default_factory=new_id)
    captured_at: datetime = field(default_factory=utc_now)
    image_ids: list[str] = field(default_factory=list)
    video_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RawImage:
    capture_id: str
    uri: str
    id: str = field(default_factory=new_id)
    mime_type: str = "image/jpeg"
    width: int | None = None
    height: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RawVideo:
    capture_id: str
    uri: str
    id: str = field(default_factory=new_id)
    mime_type: str = "video/mp4"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MappingArtifact:
    capture_id: str
    type: ArtifactType
    uri: str
    mime_type: str
    id: str = field(default_factory=new_id)
    crs: str | None = None
    bounds: tuple[float, float, float, float] | None = None
    transform: tuple[float, float, float, float, float, float] | None = None
    width: int | None = None
    height: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class Tile:
    capture_id: str
    artifact_id: str
    x_offset: int
    y_offset: int
    width: int
    height: int
    overlap: int
    parent_width: int
    parent_height: int
    transform: tuple[float, float, float, float, float, float] | None
    crs: str | None


@dataclass(slots=True)
class Orthomosaic(MappingArtifact):
    type: ArtifactType = field(default=ArtifactType.ORTHOMOSAIC, init=False)


@dataclass(slots=True)
class ElevationModel(MappingArtifact):
    type: ArtifactType = field(default=ArtifactType.DEM, init=False)


@dataclass(frozen=True, slots=True)
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.width / 2, self.y + self.height / 2


@dataclass(slots=True)
class Detection:
    capture_id: str
    class_name: str
    confidence: float
    bbox_pixel: BoundingBox
    source_width: int
    source_height: int
    source_artifact_id: str
    model_name: str
    model_version: str
    id: str = field(default_factory=new_id)
    geometry_geo: GeoJSON | None = None
    centroid_geo: GeoJSON | None = None
    timestamp: datetime = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Segmentation:
    capture_id: str
    class_name: str
    confidence: float
    geometry_geo: GeoJSON | None
    source_artifact_id: str
    model_name: str
    model_version: str
    id: str = field(default_factory=new_id)
    mask_uri: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TrackPoint:
    timestamp: datetime
    geometry_geo: GeoJSON
    detection_id: str | None = None


@dataclass(slots=True)
class Track:
    site_id: str
    class_name: str
    points: list[TrackPoint]
    id: str = field(default_factory=new_id)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ChangeEvent:
    site_id: str
    before_capture_id: str
    after_capture_id: str
    type: str
    confidence: float
    id: str = field(default_factory=new_id)
    geometry_geo: GeoJSON | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class DroneTelemetry:
    drone_id: str
    latitude: float
    longitude: float
    altitude_m: float
    heading_deg: float | None = None
    ground_speed_mps: float | None = None
    battery_percent: float | None = None
    gps_fix: str | None = None
    flight_mode: str | None = None
    timestamp: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class MissionWaypoint:
    latitude: float
    longitude: float
    altitude_m: float
    speed_m_s: float | None = None


@dataclass(slots=True)
class Mission:
    site_id: str
    drone_id: str
    waypoints: list[MissionWaypoint]
    id: str = field(default_factory=new_id)
    state: str = "planned"


@dataclass(slots=True)
class ProcessingArtifact:
    job_id: str
    artifact_id: str
    role: str
    id: str = field(default_factory=new_id)


@dataclass(slots=True)
class ModelRun:
    model_name: str
    model_version: str
    weights_uri: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=new_id)
    started_at: datetime = field(default_factory=utc_now)
    completed_at: datetime | None = None


@dataclass(slots=True)
class ProcessingJob:
    capture_id: str
    id: str = field(default_factory=new_id)
    job_type: str = "capture_pipeline"
    state: ProcessingState = ProcessingState.PENDING
    current_step: str = "CaptureUploaded"
    attempts: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    input_artifact_ids: list[str] = field(default_factory=list)
    output_artifact_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    artifacts: list[ProcessingArtifact] = field(default_factory=list)  # API compatibility
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
