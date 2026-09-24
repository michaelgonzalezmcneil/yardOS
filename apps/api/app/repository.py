from __future__ import annotations

from typing import Sequence

from sqlalchemy import delete
from sqlalchemy.orm import Session

from packages.contracts import (
    Detection as ContractDetection,
    MappingArtifact as ContractArtifact,
    ProcessingJob as ContractJob,
    ProcessingState,
    Segmentation as ContractSegmentation,
    Track as ContractTrack,
    ChangeEvent as ContractChangeEvent,
)

from . import models


def _coordinates(geometry: dict | None) -> tuple[float, float] | None:
    if not geometry or geometry.get("type") != "Point":
        return None
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    return float(coordinates[0]), float(coordinates[1])


def _wkt(geometry: dict | None) -> str | None:
    point = _coordinates(geometry)
    if point:
        return f"POINT({point[0]} {point[1]})"
    return None


class SqlAlchemyRepository:
    """Persistence adapter from canonical YardOS contracts to application tables."""

    def __init__(self, session: Session):
        self.session = session

    def save_job(self, job: ContractJob) -> None:
        row = self.session.get(models.ProcessingJob, job.id)
        if row is None:
            row = models.ProcessingJob(id=job.id, capture_id=job.capture_id)
            self.session.add(row)
        row.state = job.state.value
        row.job_type = job.job_type
        row.current_step = job.current_step
        row.attempts = job.attempts
        row.started_at = job.started_at
        row.completed_at = job.completed_at
        row.error = job.error
        row.input_artifact_ids = job.input_artifact_ids
        row.output_artifact_ids = job.output_artifact_ids
        row.metadata_json = job.metadata
        row.metadata_json = job.metadata
        row.created_at = job.created_at
        row.updated_at = job.updated_at

        capture = self.session.get(models.Capture, job.capture_id)
        if capture:
            capture.status = self._capture_status(job)
            capture.processing_error = job.error

        if job.artifacts:
            self.session.execute(delete(models.ProcessingArtifact).where(models.ProcessingArtifact.job_id == job.id))
            self.session.add_all(models.ProcessingArtifact(id=item.id, job_id=job.id, artifact_id=item.artifact_id, role=item.role) for item in job.artifacts)
        self.session.commit()

    @staticmethod
    def _capture_status(job: ContractJob) -> str:
        if job.state == ProcessingState.SUCCEEDED:
            return "complete"
        if job.state == ProcessingState.FAILED:
            return "failed"
        if job.current_step == "RunPhotogrammetry":
            return "mapping"
        if job.current_step == "RunDetection":
            return "detecting"
        if job.current_step in {"RunSegmentation", "GeoreferenceResults", "PersistResult"}:
            return "analyzing"
        return "processing"

    def save_artifacts(self, artifacts: Sequence[ContractArtifact]) -> None:
        for item in artifacts:
            row = self.session.get(models.MappingArtifact, item.id)
            if row is None:
                row = models.MappingArtifact(id=item.id, capture_id=item.capture_id, type=item.type.value, uri=item.uri, mime_type=item.mime_type)
                self.session.add(row)
            row.type = item.type.value
            row.uri = item.uri
            row.mime_type = item.mime_type
            row.crs = item.crs
            row.bounds = {"west": item.bounds[0], "south": item.bounds[1], "east": item.bounds[2], "north": item.bounds[3]} if item.bounds else None
            row.transform = list(item.transform) if item.transform else None
            row.width = item.width
            row.height = item.height
            row.metadata_json = item.metadata
            row.created_at = item.created_at
            if item.type.value == "orthomosaic":
                capture = self.session.get(models.Capture, item.capture_id)
                if capture:
                    capture.orthomosaic_url = item.uri
                    capture.orthomosaic_crs = item.crs
                    capture.orthomosaic_transform = {"coefficients": list(item.transform)} if item.transform else None
        self.session.commit()

    def save_detections(self, detections: Sequence[ContractDetection]) -> None:
        for item in detections:
            point = _coordinates(item.centroid_geo)
            if point is None:
                raise ValueError(f"Detection {item.id} is missing a geographic centroid")
            longitude, latitude = point
            row = self.session.get(models.Detection, item.id)
            if row is None:
                row = models.Detection(id=item.id, capture_id=item.capture_id, class_name=item.class_name, confidence=item.confidence, bbox={})
                self.session.add(row)
            row.class_name = item.class_name
            row.confidence = item.confidence
            row.bbox = {"x": item.bbox_pixel.x, "y": item.bbox_pixel.y, "width": item.bbox_pixel.width, "height": item.bbox_pixel.height}
            row.longitude = longitude
            row.latitude = latitude
            row.geometry = _wkt(item.centroid_geo)
            row.timestamp = item.timestamp
            row.source_artifact_id = item.source_artifact_id
            row.source_width = item.source_width
            row.source_height = item.source_height
            row.model_name = item.model_name
            row.model_version = item.model_version
        self.session.commit()

    def save_segmentations(self, segmentations: Sequence[ContractSegmentation]) -> None:
        for item in segmentations:
            row = self.session.get(models.Segmentation, item.id)
            if row is None:
                row = models.Segmentation(id=item.id, capture_id=item.capture_id, class_name=item.class_name, confidence=item.confidence, source_artifact_id=item.source_artifact_id, model_name=item.model_name, model_version=item.model_version)
                self.session.add(row)
            row.class_name = item.class_name
            row.confidence = item.confidence
            row.geometry = _wkt(item.geometry_geo)
            row.mask_uri = item.mask_uri
            row.source_artifact_id = item.source_artifact_id
            row.model_name = item.model_name
            row.model_version = item.model_version
            row.metadata_json = item.metadata
        self.session.commit()

    def save_tracks(self, tracks: Sequence[ContractTrack]) -> None:
        for item in tracks:
            if not item.points:
                continue
            row = self.session.get(models.Track, item.id)
            if row is None:
                row = models.Track(id=item.id, site_id=item.site_id, class_name=item.class_name, first_seen=item.points[0].timestamp, last_seen=item.points[-1].timestamp)
                self.session.add(row)
            row.class_name = item.class_name
            row.first_seen = min(point.timestamp for point in item.points)
            row.last_seen = max(point.timestamp for point in item.points)
            coordinates = [point.geometry_geo.get("coordinates") for point in item.points]
            coordinates = [point for point in coordinates if isinstance(point, list) and len(point) >= 2]
            row.geometry = "LINESTRING(" + ",".join(f"{point[0]} {point[1]}" for point in coordinates) + ")" if len(coordinates) > 1 else None
        self.session.commit()

    def save_change_events(self, events: Sequence[ContractChangeEvent]) -> None:
        for item in events:
            row = self.session.get(models.ChangeEvent, item.id)
            if row is None:
                row = models.ChangeEvent(id=item.id, site_id=item.site_id, before_capture_id=item.before_capture_id, after_capture_id=item.after_capture_id, type=item.type, confidence=item.confidence)
                self.session.add(row)
            row.type = item.type
            row.confidence = item.confidence
            row.geometry = _wkt(item.geometry_geo)
            row.created_at = item.created_at
        self.session.commit()
