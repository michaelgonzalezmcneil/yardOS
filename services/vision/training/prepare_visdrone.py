#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


# Official VisDrone DET IDs. YardOS intentionally bootstraps only vehicle classes.
VISDRONE_TO_YOLO = {4: 0, 5: 1, 6: 2, 9: 3}
CLASS_NAMES = ["car", "van", "truck", "bus"]


def convert_annotation(line: str, image_width: int, image_height: int) -> str | None:
    fields = line.strip().rstrip(",").split(",")
    if len(fields) < 8:
        return None
    left, top, width, height = map(float, fields[:4])
    score, category = int(fields[4]), int(fields[5])
    if score == 0 or category not in VISDRONE_TO_YOLO or width <= 0 or height <= 0:
        return None
    center_x = (left + width / 2) / image_width
    center_y = (top + height / 2) / image_height
    values = (center_x, center_y, width / image_width, height / image_height)
    clipped = tuple(min(1.0, max(0.0, value)) for value in values)
    return f"{VISDRONE_TO_YOLO[category]} " + " ".join(f"{value:.6f}" for value in clipped)


def prepare_split(source: Path, destination: Path, split: str) -> tuple[int, int]:
    from PIL import Image

    images_dir, annotations_dir = source / "images", source / "annotations"
    target_images, target_labels = destination / "images" / split, destination / "labels" / split
    target_images.mkdir(parents=True, exist_ok=True)
    target_labels.mkdir(parents=True, exist_ok=True)
    image_count = annotation_count = 0
    for image_path in sorted(path for path in images_dir.iterdir() if path.suffix.lower() in {".jpg", ".jpeg", ".png"}):
        annotation_path = annotations_dir / f"{image_path.stem}.txt"
        if not annotation_path.exists():
            continue
        with Image.open(image_path) as image:
            labels = [label for line in annotation_path.read_text().splitlines() if (label := convert_annotation(line, image.width, image.height))]
        shutil.copy2(image_path, target_images / image_path.name)
        (target_labels / f"{image_path.stem}.txt").write_text("\n".join(labels) + ("\n" if labels else ""))
        image_count += 1
        annotation_count += len(labels)
    return image_count, annotation_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert official VisDrone DET annotations to a four-class YOLO dataset.")
    parser.add_argument("--raw-dir", type=Path, default=Path(os.getenv("VISDRONE_RAW_DIR", "./datasets/raw")))
    parser.add_argument("--output-dir", type=Path, default=Path(os.getenv("VISION_DATASETS_DIR", "./datasets")) / "visdrone-yardos")
    args = parser.parse_args()
    split_sources = {"train": args.raw_dir / "VisDrone2019-DET-train", "val": args.raw_dir / "VisDrone2019-DET-val"}
    for split, source in split_sources.items():
        if not source.exists():
            raise SystemExit(f"Missing {source}. Download and extract the official VisDrone DET {split} set first.")
        images, annotations = prepare_split(source, args.output_dir, split)
        print(f"{split}: {images} images, {annotations} retained vehicle annotations")
    dataset_yaml = args.output_dir / "dataset.yaml"
    dataset_yaml.write_text(
        f"path: {args.output_dir.resolve()}\ntrain: images/train\nval: images/val\nnames:\n"
        + "".join(f"  {index}: {name}\n" for index, name in enumerate(CLASS_NAMES))
    )
    print(f"Wrote {dataset_yaml}")


if __name__ == "__main__":
    main()
