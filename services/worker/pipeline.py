from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Sequence

from packages.contracts import (
    ArtifactType,
    Capture,
    Detection,
    DetectorProvider,
    MappingArtifact,
    PhotogrammetryProvider,
    ProcessingArtifact,
    ProcessingJob,
    ProcessingState,
    Segmentation,
    SegmentationProvider,
)
from packages.database import Repository
from packages.events import Event, EventBus
from packages.geo import georeference_detection
from packages.observability import get_logger, log_context
from services.ingestion import CaptureValidator, MetadataExtractor

logger = get_logger(__name__)


@dataclass(slots=True)
class PipelineResult:
    job: ProcessingJob
    artifacts: list[MappingArtifact]
    detections: list[Detection]
    segmentations: list[Segmentation]


class CapturePipeline:
    """YardOS-owned orchestration. No upstream response model crosses this boundary."""

    def __init__(
        self,
        photogrammetry: PhotogrammetryProvider,
        detector: DetectorProvider,
        segmentation: SegmentationProvider,
        repository: Repository,
        events: EventBus,
        *,
        metadata_extractor: MetadataExtractor | None = None,
        validator: CaptureValidator | None = None,
        poll_interval_seconds: float = 2,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.photogrammetry = photogrammetry
        self.detector = detector
        self.segmentation = segmentation
        self.repository = repository
        self.events = events
        self.metadata_extractor = metadata_extractor or MetadataExtractor()
        self.validator = validator or CaptureValidator()
        self.poll_interval_seconds = poll_interval_seconds
        self.sleep = sleep

    def run(self, capture: Capture, image_uris: Sequence[str]) -> PipelineResult:
        job = ProcessingJob(capture_id=capture.id, state=ProcessingState.RUNNING)
        self.repository.save_job(job)
        self._emit("CaptureUploaded", job, {"image_count": len(image_uris)})
        try:
            with log_context(job_id=job.id, capture_id=capture.id):
                self._step(job, "ExtractMetadata")
                capture.metadata.update(self.metadata_extractor.extract(image_uris))

                self._step(job, "ValidateCapture")
                self.validator.validate(capture, image_uris)

                self._step(job, "RunPhotogrammetry")
                provider_job_id = self.photogrammetry.process_capture(capture, image_uris)
                self._wait_for_mapping(provider_job_id)
                artifacts = self.photogrammetry.get_artifacts(provider_job_id, capture)
                orthomosaic = next((item for item in artifacts if item.type == ArtifactType.ORTHOMOSAIC), None)
                if orthomosaic is None:
                    raise RuntimeError("Photogrammetry completed without an orthomosaic")
                self._emit("OrthomosaicReady", job, {"artifact_id": orthomosaic.id})

                self._step(job, "GenerateTiles")
                tiles = self._generate_tiles(orthomosaic)
                artifacts.extend(tiles)

                self._step(job, "RunDetection")
                detections = self.detector.detect_tiles(tiles)
                self._step(job, "RunSegmentation")
                segmentations = self.segmentation.segment_tiles(tiles)

                self._step(job, "GeoreferenceResults")
                source_by_id = {item.id: item for item in artifacts}
                detections = [georeference_detection(item, source_by_id[item.source_artifact_id]) for item in detections]

                self._step(job, "PersistResult")
                self.repository.save_artifacts(artifacts)
                self.repository.save_detections(detections)
                self.repository.save_segmentations(segmentations)
                job.artifacts = [ProcessingArtifact(job_id=job.id, artifact_id=item.id, role=item.type.value) for item in artifacts]
                job.state = ProcessingState.SUCCEEDED
                job.updated_at = datetime.now(timezone.utc)
                self.repository.save_job(job)
                self._emit("CaptureProcessingCompleted", job, {"detections": len(detections), "segmentations": len(segmentations)})
                return PipelineResult(job, artifacts, detections, segmentations)
        except Exception as error:
            job.state = ProcessingState.FAILED
            job.error = str(error)
            job.updated_at = datetime.now(timezone.utc)
            self.repository.save_job(job)
            self._emit("CaptureProcessingFailed", job, {"error": str(error)})
            raise

    def _wait_for_mapping(self, provider_job_id: str) -> None:
        while True:
            status = self.photogrammetry.get_status(provider_job_id)
            if status["state"] == "completed":
                return
            if status["state"] in {"failed", "canceled"}:
                raise RuntimeError(f"Photogrammetry failed: {status.get('error') or status['state']}")
            self.sleep(self.poll_interval_seconds)

    @staticmethod
    def _generate_tiles(orthomosaic: MappingArtifact) -> list[MappingArtifact]:
        # Tile creation is an adapter boundary. This identity tile keeps the DAG testable;
        # production Raster Vision emits many artifacts with pixel offsets in metadata.
        return [MappingArtifact(capture_id=orthomosaic.capture_id, type=ArtifactType.TILE, uri=f"{orthomosaic.uri}#tile=0,0", mime_type=orthomosaic.mime_type, crs=orthomosaic.crs, bounds=orthomosaic.bounds, transform=orthomosaic.transform, width=orthomosaic.width, height=orthomosaic.height, metadata={"source_artifact_id": orthomosaic.id, "pixel_offset": [0, 0]})]

    def _step(self, job: ProcessingJob, name: str) -> None:
        job.current_step = name
        job.updated_at = datetime.now(timezone.utc)
        self.repository.save_job(job)
        self._emit(name, job)
        logger.info("processing_step")

    def _emit(self, event_type: str, job: ProcessingJob, payload: dict | None = None) -> None:
        self.events.publish(Event(type=event_type, aggregate_id=job.capture_id, payload={"job_id": job.id, **(payload or {})}))
