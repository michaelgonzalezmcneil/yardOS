# YardOS documentation guide

Use this page as the starting point for understanding how YardOS works.

## Start here

1. **`/README.md`** — local setup, end-to-end test scan flow, and vision service usage.
2. **`/ARCHITECTURE.md`** — canonical product architecture and processing branches (stills vs video).
3. **`/docs/SYSTEM_ARCHITECTURE.md`** — system boundary and job-step view for orchestration and persistence.

## Supporting docs

- **`/docs/PROVIDERS.md`** — provider interfaces, adapter boundaries, and environment selection.
- **`/docs/DEPENDENCY_GRAPH.md`** — dependency direction and contracts between runtime components.
- **`/docs/OPEN_SOURCE_LICENSES.md`** — service isolation and OSS licensing boundaries.
- **`/THIRD_PARTY_LICENSES.md`** — third-party package/license inventory.
- **`/services/vision/training/datasets/yardos/README.md`** — expected layout for YardOS-labeled training data.

## Core pipeline (canonical)

```text
DJI drone photos
  -> NodeODM photogrammetry
  -> one georeferenced yard map (orthomosaic)
  -> YOLO aerial detection
  -> VisDrone bootstrap understanding (car/van/truck/bus)
  -> fine-tuning on Houston yard labels
  -> YardOS-specific classes (trailer/container/tractor/chassis/heavy_equipment/car)
```

Still imagery and video frames intentionally branch earlier in the flow, then normalize into the same georeferenced YardOS detection contract before storage and API usage.
