from packages.contracts import Detection, MappingArtifact


def georeference_detection(detection: Detection, artifact: MappingArtifact) -> Detection:
    """Attach a GeoJSON centroid using the artifact's GDAL affine transform."""
    if artifact.transform is None or artifact.crs is None:
        return detection
    x, y = detection.bbox_pixel.center
    a, b, c, d, e, f = artifact.transform
    geo_x, geo_y = a + b * x + c * y, d + e * x + f * y
    detection.centroid_geo = {"type": "Point", "coordinates": [geo_x, geo_y], "crs": artifact.crs}
    return detection
