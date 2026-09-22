# YardOS labeled dataset

This directory is a placeholder for future Houston-yard annotations. Images and labels are ignored by Git.

Use YOLO detection format:

```text
yardos/
  images/
    train/
    val/
  labels/
    train/
    val/
  dataset.yaml
```

Each label row is `class_id center_x center_y width height`, normalized to 0–1. Keep the same base filename for each image and label file.

Planned class order:

```text
0 trailer
1 shipping_container
2 tractor
3 chassis
4 heavy_equipment
5 car
```

Create `dataset.yaml` by copying `training/yardos.dataset.example.yaml`, then change `path` to the local dataset directory. Do not mix VisDrone class IDs with YardOS class IDs; bootstrap on VisDrone first, then fine-tune a compatible detection head on this six-class dataset.
