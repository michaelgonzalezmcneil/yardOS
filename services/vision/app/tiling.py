from __future__ import annotations

from collections.abc import Iterable

from .domain import Detection


def tile_windows(width: int, height: int, tile_size: int = 1024, overlap: int = 128) -> list[tuple[int, int, int, int]]:
    if tile_size <= 0 or overlap < 0 or overlap >= tile_size:
        raise ValueError("tile_size must be positive and overlap must be in [0, tile_size).")
    step = tile_size - overlap
    xs = list(range(0, max(width - tile_size, 0) + 1, step))
    ys = list(range(0, max(height - tile_size, 0) + 1, step))
    last_x, last_y = max(width - tile_size, 0), max(height - tile_size, 0)
    if not xs or xs[-1] != last_x:
        xs.append(last_x)
    if not ys or ys[-1] != last_y:
        ys.append(last_y)
    return [(x, y, min(x + tile_size, width), min(y + tile_size, height)) for y in ys for x in xs]


def intersection_over_union(a: Detection, b: Detection) -> float:
    ax1, ay1, ax2, ay2 = a.xyxy
    bx1, by1, bx2, by2 = b.xyxy
    intersection = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(0.0, min(ay2, by2) - max(ay1, by1))
    if intersection == 0:
        return 0.0
    return intersection / (a.width * a.height + b.width * b.height - intersection)


def non_max_suppression(detections: Iterable[Detection], iou_threshold: float = 0.5) -> list[Detection]:
    remaining = sorted(detections, key=lambda item: item.confidence, reverse=True)
    kept: list[Detection] = []
    while remaining:
        candidate = remaining.pop(0)
        kept.append(candidate)
        remaining = [item for item in remaining if item.class_name != candidate.class_name or intersection_over_union(candidate, item) <= iou_threshold]
    return kept


def detect_tiled(image, provider, tile_size: int = 1024, overlap: int = 128, iou_threshold: float = 0.5) -> list[Detection]:
    detections: list[Detection] = []
    for left, top, right, bottom in tile_windows(image.width, image.height, tile_size, overlap):
        tile = image.crop((left, top, right, bottom))
        detections.extend(item.translated(left, top) for item in provider.detect_image(tile))
    return non_max_suppression(detections, iou_threshold)
