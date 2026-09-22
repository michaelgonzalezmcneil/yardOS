# Dependency graph

This is the code-level interpretation of the runtime/training diagram. Arrows mean “depends on” or “produces input for.” External projects remain behind adapters.

```text
YardOS
├── runtime
│   ├── PhotogrammetryProvider ──> NodeODM / ODM
│   │   └── MappingArtifact ──> geospatial tiling ──> PostGIS
│   ├── DetectorProvider ──> MMDetection / RTMDet
│   │   └── Detection[] ──┬─> SegmentationProvider
│   │                     └─> TrackingProvider ──> Geo-trax
│   └── ChangeDetectionProvider ──> Open-CD
│       └── ChangeEvent[] ──> PostGIS
├── training
│   ├── VisDrone (generic aerial bootstrap only)
│   ├── TorchGeo / dataset utilities
│   └── Houston yard labels (YardOS-specific classes)
└── separate flight-control boundary
    └── DroneProvider ──> MAVSDK ──> PX4
```

The runtime does **not** import training datasets. Segmentation and tracking consume YardOS canonical artifacts/detections rather than MMDetection or Open-CD-native objects. Raster Vision and TorchGeo are optional implementation choices, not core domain dependencies.

## Allowed dependency direction

```text
apps/services -> packages/contracts
worker -> provider protocols + repositories + event bus
adapters -> third-party SDK/API
frontend -> YardOS API only
```

Forbidden directions include frontend-to-model coupling, ODM-to-detector calls, model adapters writing directly to PostGIS, or business logic importing third-party result classes.
