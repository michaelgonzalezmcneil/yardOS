from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Tile:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class RasterReference:
    """GDAL affine coefficients and their explicit source CRS."""
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float
    source_crs: str

    def pixel_to_projected(self, column: float, row: float) -> tuple[float, float]:
        return self.a * column + self.b * row + self.c, self.d * column + self.e * row + self.f


class TileService:
    def __init__(self, tile_size: int = 1024, overlap: int = 128):
        if tile_size <= 0 or overlap < 0 or overlap >= tile_size:
            raise ValueError("tile_size must be positive and overlap must be in [0, tile_size)")
        self.tile_size, self.overlap = tile_size, overlap

    def windows(self, width: int, height: int) -> list[Tile]:
        step = self.tile_size - self.overlap
        xs = list(range(0, max(width - self.tile_size, 0) + 1, step)) or [0]
        ys = list(range(0, max(height - self.tile_size, 0) + 1, step)) or [0]
        if xs[-1] != max(width - self.tile_size, 0): xs.append(max(width - self.tile_size, 0))
        if ys[-1] != max(height - self.tile_size, 0): ys.append(max(height - self.tile_size, 0))
        return [Tile(x, y, min(self.tile_size, width - x), min(self.tile_size, height - y)) for y in ys for x in xs]


class GeoReferenceService:
    def __init__(self, reference: RasterReference, transformer: Callable[[float, float], tuple[float, float]] | None = None):
        self.reference = reference
        if transformer is not None:
            self.transform = transformer
        elif reference.source_crs.upper() in {"EPSG:4326", "OGC:CRS84"}:
            self.transform = lambda x, y: (x, y)
        else:
            try:
                from pyproj import Transformer
            except ImportError as error:
                raise RuntimeError("pyproj is required to transform non-WGS84 orthomosaics") from error
            projection = Transformer.from_crs(reference.source_crs, "EPSG:4326", always_xy=True)
            self.transform = projection.transform

    @classmethod
    def from_geotiff(cls, path: str) -> "GeoReferenceService":
        try:
            import rasterio
        except ImportError as error:
            raise RuntimeError("rasterio is required to read GeoTIFF georeferencing") from error
        with rasterio.open(path) as dataset:
            if dataset.crs is None:
                raise ValueError(f"GeoTIFF has no CRS: {path}")
            t = dataset.transform
            reference = RasterReference(t.a, t.b, t.c, t.d, t.e, t.f, dataset.crs.to_string())
        return cls(reference)

    def pixel_to_geo(self, column: float, row: float) -> tuple[float, float]:
        projected_x, projected_y = self.reference.pixel_to_projected(column, row)
        longitude, latitude = self.transform(projected_x, projected_y)
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise ValueError("Coordinate transformation did not produce valid WGS84 longitude/latitude")
        return longitude, latitude


def _iou(first: dict, second: dict) -> float:
    a, b = first["bbox"], second["bbox"]
    ax2, ay2 = a["x"] + a["width"], a["y"] + a["height"]
    bx2, by2 = b["x"] + b["width"], b["y"] + b["height"]
    intersection = max(0, min(ax2, bx2) - max(a["x"], b["x"])) * max(0, min(ay2, by2) - max(a["y"], b["y"]))
    return intersection / (a["width"] * a["height"] + b["width"] * b["height"] - intersection) if intersection else 0


def suppress_duplicates(detections: list[dict], threshold: float = 0.5) -> list[dict]:
    remaining = sorted(detections, key=lambda item: item["confidence"], reverse=True)
    kept = []
    while remaining:
        candidate = remaining.pop(0)
        kept.append(candidate)
        remaining = [item for item in remaining if item["class"] != candidate["class"] or _iou(candidate, item) <= threshold]
    return kept


class InferencePipeline:
    def __init__(self, detector, tile_service: TileService, geo_service: GeoReferenceService, nms_iou: float = 0.5):
        self.detector, self.tile_service, self.geo_service, self.nms_iou = detector, tile_service, geo_service, nms_iou

    def run(self, image):
        detections = []
        for tile in self.tile_service.windows(image.width, image.height):
            crop = image.crop((tile.x, tile.y, tile.x + tile.width, tile.y + tile.height))
            for raw in self.detector.detect_image(crop):
                detection = deepcopy(raw) if isinstance(raw, dict) else {"class": raw.class_name, "confidence": raw.confidence, "bbox": {"x": raw.x, "y": raw.y, "width": raw.width, "height": raw.height}}
                detection["bbox"]["x"] += tile.x
                detection["bbox"]["y"] += tile.y
                detections.append(detection)
        detections = suppress_duplicates(detections, self.nms_iou)
        for detection in detections:
            bbox = detection["bbox"]
            longitude, latitude = self.geo_service.pixel_to_geo(bbox["x"] + bbox["width"] / 2, bbox["y"] + bbox["height"] / 2)
            detection.update({"longitude": longitude, "latitude": latitude})
        return detections
