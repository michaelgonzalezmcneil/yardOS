from __future__ import annotations

from typing import Callable, Sequence

from packages.contracts import BoundingBox, Detection, MappingArtifact


class MockDetectorProvider:
    model_name = "yardos-mock-detector"
    model_version = "1"

    def detect_image(self, artifact: MappingArtifact) -> list[Detection]:
        width, height = artifact.width or 1024, artifact.height or 1024
        return [Detection(capture_id=artifact.capture_id, class_name="truck", confidence=0.94, bbox_pixel=BoundingBox(width * .34, height * .38, width * .12, height * .06), source_width=width, source_height=height, source_artifact_id=artifact.id, model_name=self.model_name, model_version=self.model_version)]

    def detect_tiles(self, artifacts: Sequence[MappingArtifact]) -> list[Detection]:
        return [detection for artifact in artifacts for detection in self.detect_image(artifact)]

    def detect_batch(self, artifacts: Sequence[MappingArtifact]) -> list[list[Detection]]:
        return [self.detect_image(artifact) for artifact in artifacts]


class MMDetectionProvider:
    """Converts an injected MMDetection runner's records into YardOS detections."""

    def __init__(self, runner: Callable[[str], list[dict]], model_name: str = "rtmdet", model_version: str = "unknown"):
        self.runner, self.model_name, self.model_version = runner, model_name, model_version

    def detect_image(self, artifact: MappingArtifact) -> list[Detection]:
        width, height = artifact.width or 0, artifact.height or 0
        return [Detection(capture_id=artifact.capture_id, class_name=row["class_name"], confidence=float(row["confidence"]), bbox_pixel=BoundingBox(**row["bbox_pixel"]), source_width=width, source_height=height, source_artifact_id=artifact.id, model_name=self.model_name, model_version=self.model_version) for row in self.runner(artifact.uri)]

    def detect_tiles(self, artifacts: Sequence[MappingArtifact]) -> list[Detection]:
        return [item for batch in self.detect_batch(artifacts) for item in batch]

    def detect_batch(self, artifacts: Sequence[MappingArtifact]) -> list[list[Detection]]:
        return [self.detect_image(artifact) for artifact in artifacts]
