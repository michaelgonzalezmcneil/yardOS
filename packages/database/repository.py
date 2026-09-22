from __future__ import annotations

from dataclasses import replace
from typing import Protocol, Sequence

from packages.contracts import Detection, MappingArtifact, ProcessingJob, Segmentation


class Repository(Protocol):
    def save_job(self, job: ProcessingJob) -> None: ...
    def save_artifacts(self, artifacts: Sequence[MappingArtifact]) -> None: ...
    def save_detections(self, detections: Sequence[Detection]) -> None: ...
    def save_segmentations(self, segmentations: Sequence[Segmentation]) -> None: ...


class InMemoryRepository:
    def __init__(self):
        self.jobs: dict[str, ProcessingJob] = {}
        self.artifacts: dict[str, MappingArtifact] = {}
        self.detections: dict[str, Detection] = {}
        self.segmentations: dict[str, Segmentation] = {}

    def save_job(self, job: ProcessingJob) -> None:
        self.jobs[job.id] = replace(job)

    def save_artifacts(self, artifacts: Sequence[MappingArtifact]) -> None:
        self.artifacts.update({item.id: item for item in artifacts})

    def save_detections(self, detections: Sequence[Detection]) -> None:
        self.detections.update({item.id: item for item in detections})

    def save_segmentations(self, segmentations: Sequence[Segmentation]) -> None:
        self.segmentations.update({item.id: item for item in segmentations})
