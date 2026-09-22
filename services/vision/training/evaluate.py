#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    from ultralytics import YOLO

    parser = argparse.ArgumentParser(description="Evaluate a YardOS aerial YOLO checkpoint.")
    parser.add_argument("--model", default=os.getenv("VISION_MODEL_PATH", "runs/yardos/aerial-bootstrap/weights/best.pt"))
    parser.add_argument("--data", default=str(Path(os.getenv("VISION_DATASETS_DIR", "./datasets")) / "visdrone-yardos" / "dataset.yaml"))
    parser.add_argument("--imgsz", type=int, default=int(os.getenv("VISION_IMAGE_SIZE", "1024")))
    args = parser.parse_args()
    metrics = YOLO(args.model).val(data=args.data, imgsz=args.imgsz)
    summary = {"map50_95": float(metrics.box.map), "map50": float(metrics.box.map50), "map75": float(metrics.box.map75)}
    output = Path("runs/yardos/evaluation.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
