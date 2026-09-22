from __future__ import annotations

from .detector import DetectionProvider
from .domain import Detection


class RTMDetDetector(DetectionProvider):
    """Optional MMDetection adapter; consumers only see normalized detections."""

    def __init__(self, config_path: str, checkpoint_path: str, device: str = "cpu", confidence: float = 0.25, class_map: dict[str, str] | None = None):
        try:
            from mmdet.apis import init_detector
        except ImportError as error:
            raise RuntimeError("Install the optional MMDetection environment to use RTMDet.") from error
        self.model = init_detector(config_path, checkpoint_path, device=device)
        self.confidence = confidence
        self.class_map = class_map or {}
        self.model_version = f"rtmdet:{checkpoint_path}"

    def detect_image(self, image) -> list[Detection]:
        from mmdet.apis import inference_detector
        result = inference_detector(self.model, image)
        predictions = result.pred_instances.cpu()
        names = self.model.dataset_meta["classes"]
        detections = []
        for box, score, label in zip(predictions.bboxes.tolist(), predictions.scores.tolist(), predictions.labels.tolist()):
            if float(score) < self.confidence:
                continue
            x1, y1, x2, y2 = box
            upstream_name = str(names[int(label)])
            detections.append(Detection(self.class_map.get(upstream_name, upstream_name), float(score), float(x1), float(y1), float(x2 - x1), float(y2 - y1)))
        return detections


class MockRTMDetDetector(DetectionProvider):
    model_version = "mock-rtmdet-v1"
    def detect_image(self, image) -> list[Detection]:
        width, height = image.size
        return [Detection("truck", 0.94, width * .4, height * .4, width * .12, height * .05)]
