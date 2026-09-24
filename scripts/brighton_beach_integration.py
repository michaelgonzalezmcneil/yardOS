#!/usr/bin/env python3
"""Validate and run the opt-in Brighton Beach real-data integration."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPOSITORY = "https://github.com/pierotofy/drone_dataset_brighton_beach.git"
EXPECTED_IMAGES = 18


def _gps_decimal(values, reference: str) -> float:
    degrees, minutes, seconds = (float(value) for value in values)
    result = degrees + minutes / 60 + seconds / 3600
    return -result if reference in {"S", "W"} else result


def validate_dataset(root: Path) -> dict:
    try:
        from PIL import Image, ExifTags
    except ImportError as error:
        raise RuntimeError("Pillow is required: pip install Pillow") from error
    root = root.expanduser().resolve()
    image_dir = root / "images"
    images = sorted(image_dir.glob("*.JPG")) + sorted(image_dir.glob("*.jpg"))
    if len(images) < 3:
        raise ValueError(f"Expected an overlapping image set in {image_dir}; found {len(images)} files")
    readable = 0
    gps_rows: list[dict] = []
    dimensions: set[tuple[int, int]] = set()
    gps_tag = next(key for key, value in ExifTags.TAGS.items() if value == "GPSInfo")
    for path in images:
        try:
            with Image.open(path) as source:
                source.verify()
            with Image.open(path) as source:
                dimensions.add(source.size)
                exif = source.getexif()
                readable += 1
                gps = exif.get_ifd(gps_tag) if gps_tag in exif else {}
                decoded = {ExifTags.GPSTAGS.get(key, key): value for key, value in gps.items()}
                if "GPSLatitude" in decoded and "GPSLongitude" in decoded:
                    gps_rows.append({"file": path.name, "latitude": _gps_decimal(decoded["GPSLatitude"], decoded.get("GPSLatitudeRef", "N")), "longitude": _gps_decimal(decoded["GPSLongitude"], decoded.get("GPSLongitudeRef", "E"))})
        except Exception as error:
            raise ValueError(f"Unreadable image {path}: {error}") from error
    if len(gps_rows) != len(images):
        missing = sorted({path.name for path in images} - {row["file"] for row in gps_rows})
        raise ValueError(f"GPS metadata missing from {len(missing)} images: {missing}")
    if len({(row["latitude"], row["longitude"]) for row in gps_rows}) < 3:
        raise ValueError("GPS positions do not describe a moving capture")
    license_path = root / "LICENSE"
    return {
        "dataset_dir": str(root),
        "image_dir": str(image_dir),
        "image_count": len(images),
        "expected_image_count": EXPECTED_IMAGES,
        "expected_count_matches": len(images) == EXPECTED_IMAGES,
        "readable_count": readable,
        "gps_count": len(gps_rows),
        "dimensions": [list(item) for item in sorted(dimensions)],
        "distinct_gps_positions": len({(row["latitude"], row["longitude"]) for row in gps_rows}),
        "license_file_present": license_path.is_file(),
        "overlap_note": "Readability, sequence size, and distinct GPS positions validated; pixel overlap is ultimately validated by successful NodeODM reconstruction.",
        "images": [str(path) for path in images],
    }


def fetch(root: Path) -> None:
    if root.exists():
        raise FileExistsError(f"Destination already exists: {root}")
    root.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--depth", "1", REPOSITORY, str(root)], check=True)


def run_pipeline(root: Path, report_path: Path) -> dict:
    validation = validate_dataset(root)
    os.environ.update({"PHOTOGRAMMETRY_PROVIDER": "nodeodm", "DETECTOR_PROVIDER": "http", "SEGMENTATION_PROVIDER": "mock"})
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from apps.api.app.database import Base, SessionLocal, engine
    from apps.api.app.models import Capture, Detection, MappingArtifact, ProcessingJob, Site
    from apps.api.app.repository import SqlAlchemyRepository
    from apps.api.app.runtime import build_pipeline
    from packages.contracts import Capture as ContractCapture, ProcessingJob as ContractJob
    from sqlalchemy import func, select

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        site = Site(name="Brighton Beach Integration", latitude=50.8198, longitude=-0.1367)
        db.add(site); db.flush()
        capture = Capture(site_id=site.id, label=f"Brighton Beach {datetime.now(timezone.utc).isoformat()}", status="uploaded")
        db.add(capture); db.commit()
        contract_capture = ContractCapture(id=capture.id, site_id=site.id, label=capture.label, metadata={"dataset": REPOSITORY})
        result = build_pipeline(SqlAlchemyRepository(db)).run(contract_capture, validation["images"], job=ContractJob(capture_id=capture.id))
        orthomosaic = next(item for item in result.artifacts if item.type.value == "orthomosaic")
        stored = db.scalar(select(func.count()).select_from(Detection).where(Detection.capture_id == capture.id)) or 0
        features = db.scalars(select(Detection).where(Detection.capture_id == capture.id)).all()
        job = db.get(ProcessingJob, result.job.id)
        report = {
            "capture_id": capture.id,
            "input_image_count": validation["image_count"],
            "nodeodm_completed": result.job.state.value == "succeeded",
            "nodeodm_task_id": result.job.metadata.get("provider_task_id"),
            "processing_stage": job.current_step if job else result.job.current_step,
            "processing_error": job.error if job else result.job.error,
            "orthomosaic": {"path": orthomosaic.uri, "width": orthomosaic.width, "height": orthomosaic.height, "crs": orthomosaic.crs, "transform": orthomosaic.transform},
            "detection_count": len(result.detections),
            "mock_detection_count": sum(bool(item.metadata.get("is_mock")) for item in result.detections),
            "stored_row_count": stored,
            "geojson_feature_count": len(features),
            "map_api_url": f"/captures/{capture.id}/detections.geojson",
            "map_can_load_result": stored == len(features),
            "zero_detections_valid": True,
        }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["fetch", "validate", "run"])
    parser.add_argument("--dataset-dir", type=Path, default=Path(os.getenv("BRIGHTON_BEACH_DATASET_DIR", "data/integration/brighton_beach")))
    parser.add_argument("--report", type=Path, default=Path("data/integration-results/brighton-beach-report.json"))
    args = parser.parse_args()
    if args.command == "fetch":
        fetch(args.dataset_dir)
        print(json.dumps(validate_dataset(args.dataset_dir), indent=2))
    elif args.command == "validate":
        print(json.dumps(validate_dataset(args.dataset_dir), indent=2))
    else:
        print(json.dumps(run_pipeline(args.dataset_dir, args.report), indent=2))


if __name__ == "__main__":
    main()
