from __future__ import annotations

import math
import random
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .models import Capture, ChangeEvent, Detection, Drone, Site, Track

SITE_ID = "houston-yard-1"
MONDAY_ID = "capture-monday"
FRIDAY_ID = "capture-friday"
CLASSES = ["car", "truck", "trailer", "shipping_container", "construction_equipment", "person"]


def generated_detections(capture_id: str, friday: bool) -> list[dict]:
    randomizer = random.Random(42)
    rows = []
    for index in range(128):
        class_name = CLASSES[index % len(CLASSES)]
        base_x = -95.3047 + (index % 16) * 0.00061 + randomizer.uniform(-0.00005, 0.00005)
        base_y = 29.7572 + (index // 16) * 0.00082 + randomizer.uniform(-0.00005, 0.00005)
        moved = friday and index % 9 == 0
        appeared = friday and index >= 122
        if friday and index in {17, 41, 89}:
            continue
        lon = base_x + (0.00045 if moved else 0)
        lat = base_y + (0.00025 if moved else 0)
        if appeared:
            lon += 0.0003
        rows.append({"id": f"{capture_id}-det-{index:03d}", "capture_id": capture_id, "class_name": class_name, "confidence": round(0.82 + (index % 16) / 100, 2), "bbox": {"x": 80 + index * 11 % 1800, "y": 40 + index * 17 % 950, "width": 62 if class_name in {"truck", "trailer"} else 28, "height": 24 if class_name != "person" else 12}, "latitude": lat, "longitude": lon, "geometry": f"POINT({lon} {lat})", "timestamp": datetime(2026, 9, 18 if friday else 14, 8, 42, tzinfo=timezone.utc), "model_version": "yardos-demo-v1"})
    return rows


def load_demo(db: Session) -> dict:
    existing = db.scalar(select(Site).where(Site.id == SITE_ID))
    if existing:
        return {"site_id": SITE_ID, "created": False}
    site = Site(id=SITE_ID, name="Houston Distribution Yard", latitude=29.7605, longitude=-95.3001, bounds={"west": -95.3054, "south": 29.7568, "east": -95.2948, "north": 29.7642})
    monday = Capture(id=MONDAY_ID, site_id=SITE_ID, label="Monday baseline", captured_at=datetime(2026, 9, 14, 8, 30, tzinfo=timezone.utc), status="complete", orthomosaic_url="/demo/monday-yard.jpg")
    friday = Capture(id=FRIDAY_ID, site_id=SITE_ID, label="Friday scan", captured_at=datetime(2026, 9, 18, 8, 42, tzinfo=timezone.utc), status="complete", orthomosaic_url="/demo/friday-yard.jpg")
    db.add_all([site, monday, friday])
    db.add_all(Detection(**row) for row in generated_detections(MONDAY_ID, False))
    db.add_all(Detection(**row) for row in generated_detections(FRIDAY_ID, True))
    for index in range(17):
        lon, lat = -95.304 + (index % 8) * 0.001, 29.7578 + (index // 8) * 0.002
        db.add(ChangeEvent(id=f"change-{index}", site_id=SITE_ID, before_capture_id=MONDAY_ID, after_capture_id=FRIDAY_ID, type="moved" if index < 11 else "appeared", confidence=0.91, geometry=f"POINT({lon} {lat})", before_image="/demo/monday-yard.jpg", after_image="/demo/friday-yard.jpg"))
    db.add(Drone(id="drone-dji-m3e", name="DJI Mavic 3E", model="Mavic 3 Enterprise", status="ready"))
    db.commit()
    return {"site_id": SITE_ID, "created": True, "detections": 253, "changes": 17}
