#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path


def main() -> None:
    from ultralytics import YOLO

    default_data = Path(os.getenv("VISION_DATASETS_DIR", "./datasets")) / "visdrone-yardos" / "dataset.yaml"
    parser = argparse.ArgumentParser(description="Fine-tune a pretrained YOLO detector for aerial YardOS classes.")
    parser.add_argument("--data", default=str(default_data))
    parser.add_argument("--model", default=os.getenv("VISION_TRAIN_MODEL", "yolo11n.pt"))
    parser.add_argument("--epochs", type=int, default=int(os.getenv("VISION_EPOCHS", "50")))
    parser.add_argument("--imgsz", type=int, default=int(os.getenv("VISION_IMAGE_SIZE", "1024")))
    parser.add_argument("--device", default=os.getenv("VISION_DEVICE", ""))
    args = parser.parse_args()
    model = YOLO(args.model)
    model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz, device=args.device or None, project="runs/yardos", name="aerial-bootstrap")


if __name__ == "__main__":
    main()
