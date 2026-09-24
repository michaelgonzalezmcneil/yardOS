from __future__ import annotations

from dataclasses import replace
from typing import Protocol, Sequence

from packages.contracts import ChangeEvent, Detection, MappingArtifact, ProcessingJob, Segmentation, Track


class Repository(Protocol):
    def save_job(self, job: ProcessingJob) -> None: ...
    def save_artifacts(self, artifacts: Sequence[MappingArtifact]) -> None: ...
    def save_detections(self, detections: Sequence[Detection]) -> None: ...
    def save_segmentations(self, segmentations: Sequence[Segmentation]) -> None: ...
    def save_tracks(self, tracks: Sequence[Track]) -> None: ...
    def save_change_events(self, events: Sequence[ChangeEvent]) -> None: ...


class InMemoryRepository:
    def __init__(self):
        self.jobs: dict[str, ProcessingJob] = {}
        self.artifacts: dict[str, MappingArtifact] = {}
        self.detections: dict[str, Detection] = {}
        self.segmentations: dict[str, Segmentation] = {}
        self.tracks: dict[str, Track] = {}
        self.change_events: dict[str, ChangeEvent] = {}

    def save_job(self, job: ProcessingJob) -> None:
        self.jobs[job.id] = replace(job)

    def save_artifacts(self, artifacts: Sequence[MappingArtifact]) -> None:
        self.artifacts.update({item.id: item for item in artifacts})

    def save_detections(self, detections: Sequence[Detection]) -> None:
        self.detections.update({item.id: item for item in detections})

    def save_segmentations(self, segmentations: Sequence[Segmentation]) -> None:
        self.segmentations.update({item.id: item for item in segmentations})

    def save_tracks(self, tracks: Sequence[Track]) -> None:
        self.tracks.update({item.id: item for item in tracks})

    def save_change_events(self, events: Sequence[ChangeEvent]) -> None:
        self.change_events.update({item.id: item for item in events})
