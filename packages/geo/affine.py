from dataclasses import replace

from packages.contracts import BoundingBox, Detection, MappingArtifact


def tile_detection_to_image(detection: Detection, tile: MappingArtifact) -> Detection:
    """Return a detection in parent-image pixels without mutating provider output."""
    offset = tile.metadata.get("pixel_offset", [0, 0])
    parent_size = tile.metadata.get("parent_size", [tile.width, tile.height])
    bbox = detection.bbox_pixel
    return replace(
        detection,
        bbox_pixel=BoundingBox(bbox.x + float(offset[0]), bbox.y + float(offset[1]), bbox.width, bbox.height),
        source_width=int(parent_size[0] or detection.source_width),
        source_height=int(parent_size[1] or detection.source_height),
        metadata={**detection.metadata, "tile_artifact_id": tile.id},
    )


def _iou(left: BoundingBox, right: BoundingBox) -> float:
    x1, y1 = max(left.x, right.x), max(left.y, right.y)
    x2 = min(left.x + left.width, right.x + right.width)
    y2 = min(left.y + left.height, right.y + right.height)
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = left.width * left.height + right.width * right.height - intersection
    return intersection / union if union else 0.0


def suppress_duplicate_detections(detections: list[Detection], threshold: float = 0.5) -> list[Detection]:
    """Class-aware NMS over canonical global-image boxes."""
    kept: list[Detection] = []
    for candidate in sorted(detections, key=lambda item: item.confidence, reverse=True):
        if all(candidate.class_name != accepted.class_name or _iou(candidate.bbox_pixel, accepted.bbox_pixel) <= threshold for accepted in kept):
            kept.append(candidate)
    return kept


def georeference_detection(detection: Detection, artifact: MappingArtifact) -> Detection:
    """Attach a GeoJSON centroid using the artifact's GDAL affine transform."""
    if artifact.transform is None or artifact.crs is None:
        return detection
    x, y = detection.bbox_pixel.center
    a, b, c, d, e, f = artifact.transform
    geo_x, geo_y = a + b * x + c * y, d + e * x + f * y
    detection.centroid_geo = {"type": "Point", "coordinates": [geo_x, geo_y], "crs": artifact.crs}
    return detection
