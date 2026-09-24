from __future__ import annotations

from pathlib import Path

from packages.contracts import Detection, MappingArtifact


def read_geotiff(path: str | Path, capture_id: str, *, artifact_id: str | None = None) -> MappingArtifact:
    try:
        import rasterio
    except ImportError as error:
        raise RuntimeError("rasterio is required to inspect NodeODM GeoTIFF output") from error
    source = Path(path).expanduser().resolve()
    with rasterio.open(source) as dataset:
        if dataset.crs is None:
            raise ValueError(f"Orthomosaic has no CRS: {source}")
        if dataset.transform.is_identity:
            raise ValueError(f"Orthomosaic has an identity affine transform: {source}")
        # Store GDAL ordering: origin-x, pixel-x, rotation-x, origin-y, rotation-y, pixel-y.
        transform = tuple(float(value) for value in dataset.transform.to_gdal())
        bounds = tuple(float(value) for value in dataset.bounds)
        artifact = MappingArtifact(
            capture_id=capture_id,
            type=__import__("packages.contracts", fromlist=["ArtifactType"]).ArtifactType.ORTHOMOSAIC,
            uri=str(source),
            mime_type="image/tiff",
            crs=dataset.crs.to_string(),
            transform=transform,
            bounds=bounds,
            width=dataset.width,
            height=dataset.height,
            metadata={"driver": dataset.driver, "bands": dataset.count},
        )
        if artifact_id:
            artifact.id = artifact_id
        return artifact


def georeference_wgs84(detection: Detection, artifact: MappingArtifact) -> Detection:
    if artifact.crs is None or artifact.transform is None:
        raise ValueError("Cannot georeference a detection without orthomosaic CRS and affine transform")
    pixel_x, pixel_y = detection.bbox_pixel.center
    origin_x, scale_x, shear_x, origin_y, shear_y, scale_y = artifact.transform
    map_x = origin_x + scale_x * pixel_x + shear_x * pixel_y
    map_y = origin_y + shear_y * pixel_x + scale_y * pixel_y
    if artifact.crs.upper() in {"EPSG:4326", "OGC:CRS84"}:
        longitude, latitude = map_x, map_y
    else:
        try:
            from pyproj import CRS, Transformer
        except ImportError as error:
            raise RuntimeError("pyproj is required to convert projected orthomosaic coordinates to WGS84") from error
        source_crs = CRS.from_user_input(artifact.crs)
        if not source_crs.is_projected and not source_crs.is_geographic:
            raise ValueError(f"Unsupported orthomosaic CRS: {artifact.crs}")
        longitude, latitude = Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True).transform(map_x, map_y)
    if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
        raise ValueError(f"Invalid WGS84 result for detection {detection.id}: {longitude}, {latitude}")
    detection.centroid_geo = {"type": "Point", "coordinates": [longitude, latitude]}
    detection.metadata["source_crs"] = artifact.crs
    return detection
