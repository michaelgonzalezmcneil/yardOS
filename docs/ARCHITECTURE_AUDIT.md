# Architecture audit

Audit date: 2026-09-23

## Existing components retained

- FastAPI API and Next.js/MapLibre web application.
- Postgres/PostGIS application schema and GeoJSON endpoints.
- NodeODM and vision HTTP integration code.
- Provider-neutral Python contracts, event bus, storage adapters, and structured logging.
- Existing vision tiling/NMS implementation and VisDrone conversion utilities.

## Changes made at the integration spine

- Completed the canonical job vocabulary and lifecycle fields, including attempts,
  input/output artifact IDs, timestamps, retry/cancel states, and metadata.
- Added canonical `Tile` and `ModelRun` contracts and completed normalized telemetry fields.
- Made tiled detector output global-image-relative before class-aware NMS and
  georeferencing; providers remain unaware of persistence.
- Extended the explicit worker DAG through tracking, prior-capture comparison,
  analytics, and `CaptureComplete` / `CaptureFailed` domain events.
- Extended repository boundaries to persist tracks and change events without giving
  adapters database access.
- Kept optional NodeODM HTTP dependencies out of the default mock import path.

## Remaining production work

- The API currently schedules the MVP pipeline as a FastAPI background task. Move the
  same `CapturePipeline` call behind a durable queue/worker adapter before relying on
  restart-safe production execution.
- MinIO/S3 adapters exist, but the API ingestion path does not yet upload raw files or
  materialize mock artifacts. Object-store initialization and lifecycle policy remain.
- Real provider smoke tests require separately installed services, weights, data, or
  hardware and stay outside the normal test suite.
- Add schema migrations before deploying the expanded processing-job fields; local
  development currently creates tables directly.
- The change provider validates capture identity at the canonical boundary, but a real
  Open-CD adapter must also record overlap, grid registration, and alignment quality.
