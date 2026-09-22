# YardOS architecture

YardOS is an operating system that converts drone data into answers about a physical site. The MVP prioritizes one demoable vertical slice over deep integration with every upstream project.

```text
YARD / SITE
     │
     ▼
DJI drone ── future flight control: PX4 + MAVSDK
     │
     ▼
photos / video / GPS
     │
     ├───────────────────────────┐
     ▼                           ▼
NodeODM                     video frames
     │                           │
     ▼                           │
orthomosaic                     │
     │                           │
     ▼                           │
overlapping tiles               │
(Raster Vision-style)           │
     │                           │
     └──────────────┬────────────┘
                    ▼
          replaceable detector
        MMDetection / RTMDet / mock
                    │
                    ▼
       georeferenced detections
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
   capture comparison     time-ordered
   Open-CD adapter        object tracking
   or MVP baseline        (future)
          └─────────┬─────────┘
                    ▼
            PostgreSQL / PostGIS
                    │
                    ▼
               YardOS API
                    │
                    ▼
          Next.js + MapLibre UI
                    │
                    ▼
  "What changed?" · "Where is truck #42?"
  "How many containers?" · "Which equipment hasn't moved?"
  "Where are the bottlenecks?"
```

This is the canonical product architecture. The diagram intentionally separates capture products:

- Geotagged still photos go through NodeODM to create the site-level orthomosaic used for inventory, location, and capture-to-capture comparison.
- Video is sampled into frames and can go directly to the detector for near-real-time observations; it does not require photogrammetry first.
- Both paths produce the same normalized detection contract before georeferencing and persistence.
- Open-CD is a future change-model adapter. The MVP baseline compares aligned captures and detected objects behind the same service interface.
- Tracking is downstream of detections and requires observations ordered over time. It is not part of the first inventory demo.

## Boundaries

- `apps/web`: customer product surface. It only consumes YardOS API shapes.
- `apps/api`: domain models, CRUD, processing orchestration, GeoJSON, demo data.
- `services/vision`: replaceable detector interface. MMDetection is optional; mock inference keeps demo mode available.
- `services/geospatial`: tiling and pixel-to-geographic transforms inspired by Raster Vision/TorchGeo concepts, without copying their internals.
- `services/change_detection`: replaceable change interface with a deterministic object-difference baseline.
- `services/drone`: simulation-first provider interface; MAVSDK commands require explicit non-default configuration.
- `packages/database`: shared SQL schema documentation and migrations.
- `packages/shared`: cross-service API contracts.
- `infra`: container configuration.

## Processing states

`uploaded → processing → mapping → detecting → analyzing → complete`, with `failed` as a terminal error state.

## MVP operating modes

- **Demo:** prepared Houston yard captures and 100+ synthetic detections. No drone, CUDA, or NodeODM required.
- **Integrated:** uploaded photos are submitted to NodeODM, the orthomosaic is tiled, inference runs, detections are georeferenced and stored.
- **Future flight:** MAVSDK/PX4 remains disabled unless `DRONE_MODE` is explicitly changed from `simulation`.
