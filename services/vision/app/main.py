from __future__ import annotations

import io
import os
import time

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from .detector import MockDetectionProvider, YOLODetectionProvider
from .schemas import BoundingBox, Center, DetectionResponse, DetectionResponseItem, HealthResponse
from .tiling import detect_tiled


def build_provider():
    provider_name = os.getenv("VISION_PROVIDER", "mock").lower()
    version = os.getenv("VISION_MODEL_VERSION", "yolo11n-visdrone-bootstrap")
    if provider_name == "mock":
        return MockDetectionProvider(os.getenv("VISION_MODEL_VERSION", "yardos-mock-v1"))
    if provider_name == "yolo":
        return YOLODetectionProvider(os.getenv("VISION_MODEL_PATH", "yolo11n.pt"), version, float(os.getenv("VISION_CONFIDENCE", "0.25")))
    raise RuntimeError(f"Unsupported VISION_PROVIDER: {provider_name}")


provider = build_provider()
app = FastAPI(title="YardOS Vision", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", provider=provider.__class__.__name__, model_version=provider.model_version)


@app.post("/detect", response_model=DetectionResponse, response_model_by_alias=True)
async def detect(file: UploadFile = File(...)) -> DetectionResponse:
    if file.content_type not in {"image/jpeg", "image/png", "image/tiff"}:
        raise HTTPException(415, "Only JPG, PNG, and NodeODM GeoTIFF uploads are supported.")
    try:
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(400, "The uploaded file is not a readable image.") from error

    tile_size = int(os.getenv("VISION_TILE_SIZE", "1024"))
    started = time.perf_counter()
    tiled = image.width > tile_size or image.height > tile_size
    detections = detect_tiled(image, provider, tile_size, int(os.getenv("VISION_TILE_OVERLAP", "128")), float(os.getenv("VISION_NMS_IOU", "0.50"))) if tiled else provider.detect_image(image)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return DetectionResponse(
        detections=[DetectionResponseItem(class_name=item.class_name, confidence=item.confidence, bbox=BoundingBox(x=item.x, y=item.y, width=item.width, height=item.height), center=Center(x=item.center[0], y=item.center[1])) for item in detections],
        image_width=image.width,
        image_height=image.height,
        model_version=provider.model_version,
        inference_time_ms=round(elapsed_ms, 3),
        tiled=tiled,
    )
