from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .domain import Detection


class DetectionProvider(ABC):
    model_version: str

    @abstractmethod
    def detect_image(self, image) -> list[Detection]:
        raise NotImplementedError

    def detect_batch(self, images) -> list[list[Detection]]:
        return [self.detect_image(image) for image in images]

    def detect_video(self, frames):
        for frame in frames:
            yield self.detect_image(frame)

    def detect(self, image) -> list[Detection]:
        return self.detect_image(image)


class YOLODetectionProvider(DetectionProvider):
    def __init__(self, model_path: str, model_version: str, confidence: float = 0.25):
        try:
            from ultralytics import YOLO
        except ImportError as error:
            raise RuntimeError("Ultralytics is not installed. Install services/vision/requirements.txt or use VISION_PROVIDER=mock.") from error
        if Path(model_path).suffix == ".pt" and Path(model_path).parent != Path(".") and not Path(model_path).exists():
            raise RuntimeError(f"YOLO checkpoint does not exist: {model_path}")
        self.model = YOLO(model_path)
        self.model_version = model_version
        self.confidence = confidence

    def detect_image(self, image) -> list[Detection]:
        result = self.model.predict(source=image, conf=self.confidence, verbose=False)[0]
        names = result.names
        detections: list[Detection] = []
        if result.boxes is None:
            return detections
        for coordinates, confidence, class_id in zip(result.boxes.xyxy.tolist(), result.boxes.conf.tolist(), result.boxes.cls.tolist()):
            x1, y1, x2, y2 = coordinates
            detections.append(Detection(str(names[int(class_id)]), float(confidence), float(x1), float(y1), float(x2 - x1), float(y2 - y1)))
        return detections


class MockDetectionProvider(DetectionProvider):
    """Deterministic demo provider. It is not presented as an ML result."""

    def __init__(self, model_version: str = "yardos-mock-v1"):
        self.model_version = model_version

    def detect_image(self, image) -> list[Detection]:
        width, height = image.size
        return [
            Detection("truck", 0.94, width * 0.34, height * 0.38, max(24, width * 0.12), max(16, height * 0.06)),
            Detection("car", 0.88, width * 0.62, height * 0.57, max(16, width * 0.06), max(12, height * 0.035)),
        ]
