from __future__ import annotations

from typing import Callable, Sequence

from packages.contracts import MappingArtifact, Segmentation


class MockSegmentationProvider:
    def segment_image(self, artifact: MappingArtifact) -> list[Segmentation]:
        return []

    def segment_tiles(self, artifacts: Sequence[MappingArtifact]) -> list[Segmentation]:
        return [item for artifact in artifacts for item in self.segment_image(artifact)]


class AerialSegmentationProvider:
    def __init__(self, runner: Callable[[str], list[dict]], model_name: str, model_version: str):
        self.runner, self.model_name, self.model_version = runner, model_name, model_version

    def segment_image(self, artifact: MappingArtifact) -> list[Segmentation]:
        return [Segmentation(capture_id=artifact.capture_id, class_name=row["class_name"], confidence=float(row["confidence"]), geometry_geo=row.get("geometry_geo"), mask_uri=row.get("mask_uri"), source_artifact_id=artifact.id, model_name=self.model_name, model_version=self.model_version) for row in self.runner(artifact.uri)]

    def segment_tiles(self, artifacts: Sequence[MappingArtifact]) -> list[Segmentation]:
        return [item for artifact in artifacts for item in self.segment_image(artifact)]
