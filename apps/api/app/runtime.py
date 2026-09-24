from __future__ import annotations

import os

from packages.contracts import Capture as ContractCapture, ProcessingJob as ContractJob
from packages.events import InMemoryEventBus
from services.photogrammetry import MockPhotogrammetryProvider, NodeODMClient, ODMPhotogrammetryProvider
from services.segmentation import MockSegmentationProvider
from services.tracking import SimpleTrackingProvider
from services.change_detection import SimpleDifferenceProvider
from services.vision.providers import MockDetectorProvider, VisionHTTPProvider
from services.worker import CapturePipeline

from .database import SessionLocal
from .repository import SqlAlchemyRepository


def build_pipeline(repository: SqlAlchemyRepository) -> CapturePipeline:
    photogrammetry_provider = os.getenv("PHOTOGRAMMETRY_PROVIDER", "mock")
    detector_provider = os.getenv("DETECTOR_PROVIDER", os.getenv("VISION_PROVIDER", "mock"))
    segmentation_provider = os.getenv("SEGMENTATION_PROVIDER", "mock")
    unsupported = {"SEGMENTATION_PROVIDER": segmentation_provider if segmentation_provider != "mock" else None}
    selected = {key: value for key, value in unsupported.items() if value}
    if selected:
        values = ", ".join(f"{key}={value}" for key, value in selected.items())
        raise RuntimeError(f"API runtime currently supports mock providers only ({values})")
    if photogrammetry_provider == "nodeodm":
        mapping = ODMPhotogrammetryProvider(NodeODMClient(os.getenv("NODEODM_HOST", "localhost"), int(os.getenv("NODEODM_PORT", "3000"))), os.getenv("NODEODM_OUTPUT_DIR", "data/integration-results/nodeodm"))
    elif photogrammetry_provider == "mock":
        mapping = MockPhotogrammetryProvider()
    else:
        raise RuntimeError(f"Unsupported PHOTOGRAMMETRY_PROVIDER={photogrammetry_provider}")
    if detector_provider in {"http", "yolo"}:
        detector = VisionHTTPProvider(os.getenv("VISION_SERVICE_URL", "http://localhost:8001"), allow_mock=os.getenv("ALLOW_MOCK_VISION", "false").lower() == "true")
    elif detector_provider == "mock":
        detector = MockDetectorProvider()
    else:
        raise RuntimeError(f"Unsupported DETECTOR_PROVIDER={detector_provider}")
    return CapturePipeline(
        mapping,
        detector,
        MockSegmentationProvider(),
        repository,
        InMemoryEventBus(),
        tracking=SimpleTrackingProvider(),
        change_detection=SimpleDifferenceProvider(),
        poll_interval_seconds=0,
    )


def run_capture_job(capture: ContractCapture, image_uris: list[str], job: ContractJob) -> None:
    with SessionLocal() as session:
        repository = SqlAlchemyRepository(session)
        try:
            build_pipeline(repository).run(capture, image_uris, job=job)
        except Exception:
            # CapturePipeline has already persisted the canonical failure state.
            return
