# YardOS canonical pipeline

This is the entire YardOS processing pipeline. Preserve this architecture unless a product decision explicitly changes it:

```text
DJI drone photos
        ↓
NodeODM photogrammetry
        ↓
one georeferenced yard map / orthomosaic
        ↓
YOLO aerial object detection
        ↓
VisDrone bootstrap understanding
  "truck here"
  "truck here"
  "car here"
        ↓
fine-tune on our own labeled Houston yard dataset
        ↓
YardOS-specific understanding
  "53-ft trailer here"
  "container here"
  "chassis here"
```

The fuller system diagram and integration boundaries live in `ARCHITECTURE.md`; treat that file as the source of truth. In particular, still imagery and video form two intentional branches: stills produce an orthomosaic through NodeODM, while sampled video frames may flow directly to the detector. Both normalize into georeferenced YardOS detections before PostGIS, change analysis, tracking, and UI queries.

## Architectural rules

- DJI/drone images are the source inputs.
- NodeODM is the production-facing photogrammetry service. It turns an overlapping image set into one yard orthomosaic and related geospatial outputs.
- YOLO analyzes the resulting yard map. Do not run detection independently on every source photo in the normal production flow.
- VisDrone is only the bootstrap dataset for aerial vehicle understanding: `car`, `van`, `truck`, and `bus`.
- Never claim that VisDrone provides YardOS-specific labels such as trailers, containers, tractors, chassis, or heavy equipment.
- The labeled Houston yard dataset is the path to YardOS-specific classes, including `trailer`, `shipping_container`, `tractor`, `chassis`, `heavy_equipment`, and `car`.
- Keep NodeODM and the FastAPI vision service isolated behind their existing service interfaces. Do not copy or reimplement their photogrammetry or neural-network internals in the YardOS application.
- Detection output must remain structured and scan-scoped: scan ID, class, confidence, bounding box, center coordinates, and model version.
- Do not add tracking, OCR, custom neural-network architectures, or infrastructure complexity until the core pipeline is working reliably.
