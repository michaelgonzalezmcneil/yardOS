from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from packages.contracts import ArtifactType, Capture, MappingArtifact, Orthomosaic


class MockPhotogrammetryProvider:
    def __init__(self):
        self.jobs: dict[str, tuple[Capture, Sequence[str]]] = {}

    def process_capture(self, capture: Capture, image_uris: Sequence[str]) -> str:
        if not image_uris:
            raise ValueError("Photogrammetry requires at least one image")
        job_id = f"mock-odm-{capture.id}"
        self.jobs[job_id] = (capture, image_uris)
        return job_id

    def get_status(self, provider_job_id: str) -> dict[str, Any]:
        if provider_job_id not in self.jobs:
            raise KeyError(provider_job_id)
        return {"state": "completed", "progress": 100}

    def get_artifacts(self, provider_job_id: str, capture: Capture) -> list[MappingArtifact]:
        self.get_status(provider_job_id)
        base = f"s3://yardos/sites/{capture.site_id}/captures/{capture.id}"
        return [
            Orthomosaic(capture_id=capture.id, uri=f"{base}/orthomosaic/orthophoto.tif", mime_type="image/tiff", crs="EPSG:4326", transform=(-95.31, 0.00001, 0.0, 29.77, 0.0, -0.00001), width=4096, height=4096, metadata={"provider": "mock"}),
            MappingArtifact(capture_id=capture.id, type=ArtifactType.POINT_CLOUD, uri=f"{base}/point-cloud/model.laz", mime_type="application/vnd.laszip", metadata={"provider": "mock"}),
        ]


class ODMPhotogrammetryProvider:
    """Adapter for a NodeODM client. The worker never sees NodeODM response shapes."""

    def __init__(self, client: Any, output_dir: str | Path = "data/integration-results/nodeodm"):
        self.client = client
        self.output_dir = Path(output_dir)

    def process_capture(self, capture: Capture, image_uris: Sequence[str]) -> str:
        return str(self.client.create_task(list(image_uris)))

    def get_status(self, provider_job_id: str) -> dict[str, Any]:
        raw = self.client.get_task(provider_job_id)
        code = int(raw.get("status", {}).get("code", raw.get("status", -1)))
        states = {10: "queued", 20: "running", 30: "failed", 40: "completed", 50: "canceled"}
        return {"state": states.get(code, "unknown"), "progress": raw.get("progress", 0), "error": raw.get("error")}

    def get_artifacts(self, provider_job_id: str, capture: Capture) -> list[MappingArtifact]:
        status = self.get_status(provider_job_id)
        if status["state"] != "completed":
            raise RuntimeError(f"ODM task {provider_job_id} is {status['state']}: {status.get('error') or ''}".strip())
        raw = self.client.download_artifacts(provider_job_id, self.output_dir)
        artifacts: list[MappingArtifact] = []
        mapping = {
            "orthomosaic": (ArtifactType.ORTHOMOSAIC, "image/tiff"),
            "dem": (ArtifactType.DEM, "image/tiff"),
            "point_cloud": (ArtifactType.POINT_CLOUD, "application/vnd.laszip"),
        }
        for name, uri in raw.items():
            if name in mapping and uri:
                kind, mime = mapping[name]
                if kind == ArtifactType.ORTHOMOSAIC:
                    from services.geospatial import read_geotiff

                    artifact = read_geotiff(uri, capture.id)
                    artifact.metadata.update({"provider": "nodeodm", "provider_job_id": provider_job_id})
                    artifacts.append(artifact)
                else:
                    artifacts.append(MappingArtifact(capture_id=capture.id, type=kind, uri=str(uri), mime_type=mime, metadata={"provider": "nodeodm", "provider_job_id": provider_job_id}))
        return artifacts
