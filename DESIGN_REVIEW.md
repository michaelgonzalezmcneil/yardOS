# YardOS Design Review

## Executive Summary

The repository has the beginnings of sound service boundaries, a useful demo fixture, and a polished product direction, but it is **not yet an end-to-end drone-processing system**. It cannot currently and reliably turn uploaded imagery into geographically correct operational intelligence. The implemented path stops at independent components: there is no upload endpoint, job runner, metadata stage, working Python-to-NodeODM adapter, database migration, or API-driven frontend flow.

The most serious correctness flaw—linear bounds-based georeferencing that ignored GeoTIFF affine transforms and CRS—was corrected during this review. Cross-tile NMS, capture-alignment enforcement, and flight-control interlocks were also tightened and tested. Those fixes make the isolated primitives safer; they do not fill in the missing orchestration.

For an investor/internal demo, the static Houston yard experience is directionally compelling. For a customer demo, the frontend must consume the same API/GeoJSON path that real captures will use, dependencies and containers must build, and the prepared orthomosaic must be bundled locally. Production readiness is substantially further away.

## What Is Correct

- Third-party systems are generally kept behind YardOS-owned modules instead of vendoring upstream repositories.
- NodeODM is represented as a separate container and the repository does not contain ODM source.
- `DetectionProvider`, `PhotogrammetryService`, `ChangeDetectionService`, and `DroneProvider` express useful replacement boundaries.
- The detector now exposes image, batch, and video entry points and normalizes MMDetection results into YardOS `Detection` objects.
- The vision tiler restores full-image coordinates and performs class-aware NMS across overlapping tiles.
- MapLibre uses a GeoJSON source/layer rather than creating one DOM marker per detection.
- Detection and Track are separate concepts. A nullable `track_id` now allows observations to be associated with a persistent physical-object track later.
- Real drone control is fail-closed behind both `DRONE_MODE=mavsdk` and `DRONE_ALLOW_REAL_FLIGHT=true`; simulation remains the default.
- The demo fixture contains two captures and more than 100 detections per capture.

## Critical Issues

### 1. No executable capture-processing workflow

**ISSUE:** `POST /captures/{id}/process` only changes a database string to `processing`. It does not extract metadata, dispatch a job, call photogrammetry, tile, infer, georeference, persist detections, generate changes, or mark failure/completion.

**WHY IT MATTERS:** The repository does not implement its core product loop. Captures become permanently stuck.

**SEVERITY:** Critical.

**RECOMMENDED FIX:** Add one in-process/background worker with an idempotent stage runner, persisted stage/status/error/attempt fields, and retry from the last completed stage. Do not add a distributed queue yet.

### 2. Photogrammetry adapters do not connect

**ISSUE:** The Python `NodeODMPhotogrammetryService` expects async `create_task`, `get_orthophoto`, and `get_asset`; the implemented NodeODM client is JavaScript and exposes different names and return shapes.

**WHY IT MATTERS:** No API code can call the existing NodeODM implementation.

**SEVERITY:** Critical.

**RECOMMENDED FIX:** Choose one runtime boundary. The fastest path is a Python NodeODM HTTP adapter implementing the exact `PhotogrammetryService` contract, with contract tests against a mock NodeODM server.

### 3. Frontend demo bypasses the API

**ISSUE:** `apps/web/lib/demo.ts` generates detections independently. Capture switching, KPI counts, object details, and comparison do not call YardOS API endpoints.

**WHY IT MATTERS:** A successful demo says nothing about the production data path; demo and real modes can silently diverge.

**SEVERITY:** Critical for customer-demo integrity.

**RECOMMENDED FIX:** Seed demo rows through `/demo/load`, then have the same frontend data client request `/sites`, captures, dashboard metrics, changes, and `detections.geojson` in both modes.

### 4. Commercial vision path includes AGPL Ultralytics

**ISSUE:** Ultralytics is an installed runtime dependency and its model/training code is active, while the stated commercial architecture prefers Apache-2.0 MMDetection.

**WHY IT MATTERS:** Upstream documents identify Ultralytics code/models as AGPL-3.0 unless an Enterprise License applies. This can create source-disclosure obligations incompatible with the intended product.

**SEVERITY:** Critical legal/product risk.

**RECOMMENDED FIX:** Remove Ultralytics from the production image and make MMDetection/RTMDet the supported detector, or obtain and record an Enterprise License. Treat all weights separately.

### 5. No authentication or authorization

**ISSUE:** Site creation, capture creation, processing, demo seeding, and all reads are public. Organization ownership is not checked.

**WHY IT MATTERS:** Any network client could inspect or mutate every customer's operational data.

**SEVERITY:** Critical before any external deployment.

**RECOMMENDED FIX:** Add authenticated principals and organization-scoped queries before exposing the API beyond localhost. Disable `/demo/load` outside demo mode.

## High-Priority Improvements

### Database lifecycle and integrity

**ISSUE:** The API calls `create_all()` at runtime and has no migrations. Relationships are mostly scalar foreign keys without ORM relationships; several domain tables lack full audit timestamps. The schema was improved with cascade behavior, status constraints, composite indexes, detection footprint, track line geometry, and raster CRS/transform fields, but these changes are not migration-backed.

**WHY IT MATTERS:** Schema evolution is unsafe and deployed databases cannot be upgraded predictably.

**SEVERITY:** High.

**RECOMMENDED FIX:** Add Alembic, create an initial PostGIS migration including `CREATE EXTENSION postgis`, and test deletes/constraints against PostgreSQL—not only SQLite.

### Detection footprints and spatial queries

**ISSUE:** Point geometry is stored, but polygon footprints are not generated from bounding boxes. GeoJSON returns only points and has no spatial index declaration in a migration.

**WHY IT MATTERS:** Map overlays cannot represent object extent and PostGIS proximity/intersection queries will degrade.

**SEVERITY:** High.

**RECOMMENDED FIX:** Transform all four bbox corners through the raster affine/CRS, store a polygon footprint plus centroid, and add GiST indexes.

### Change baseline has no identity strategy

**ISSUE:** `ObjectDifferenceBaseline` compares record IDs, but demo detection IDs include the capture ID and therefore never match across captures. It is object-observation difference, not semantic image change or pixel difference.

**WHY IT MATTERS:** Real change results would classify nearly everything as appeared/disappeared.

**SEVERITY:** High.

**RECOMMENDED FIX:** For MVP, explicitly match same-class detections by geographic distance/IoU after alignment. Keep Open-CD behind a separate semantic-change adapter.

### Unbounded image memory and request sizes

**ISSUE:** `/detect` reads the full upload into memory and converts the entire GeoTIFF to RGB before tiling. The Node client also buffers images for upload and can buffer up to 1 GB while extracting ZIP data.

**WHY IT MATTERS:** Large orthomosaics can exhaust memory or provide a denial-of-service vector.

**SEVERITY:** High.

**RECOMMENDED FIX:** Enforce byte/pixel limits; store uploads to a controlled directory/object store; use Rasterio window reads; stream ZIP extraction; validate format by decoding, not only MIME type.

### Demo requires an external basemap

**ISSUE:** MapLibre loads Esri World Imagery from the public network.

**WHY IT MATTERS:** `docker compose up` does not provide a fully self-contained demo and may violate tile-service usage/attribution requirements.

**SEVERITY:** High for demo reliability.

**RECOMMENDED FIX:** Bundle the prepared demo orthomosaic as a georeferenced MapLibre image/raster source; keep external basemaps optional and attributed.

### GeoJSON has no bounds or pagination

**ISSUE:** The endpoint returns all capture detections in one response.

**WHY IT MATTERS:** 100,000 records produce slow queries, large JSON payloads, and browser stalls.

**SEVERITY:** High at operational scale.

**RECOMMENDED FIX:** Accept bbox/zoom/class filters, query PostGIS spatially, and return vector tiles or bounded GeoJSON. The current MapLibre source/layer is suitable for thousands, not unbounded datasets.

## Low-Priority Improvements

- Add typed frontend API clients, loading/empty/error states, and abortable capture requests.
- Replace semicolon-compressed API handlers with conventional formatting and structured service methods.
- Pin Docker image digests and application dependency versions rather than broad ranges/`latest`.
- Add structured logs with capture/task correlation IDs.
- Add health/readiness checks for API, web, vision, database, and optional NodeODM.
- Remove unused imports and incomplete directory claims (`packages/*`, `infra/`) until those paths actually exist.
- Add rate limiting and response compression after the core flow exists.

## Licensing Risks

- **Ultralytics: REQUIRES LEGAL REVIEW / production blocker.** Upstream offers AGPL-3.0 or an Enterprise License.
- **NodeODM and ODM: REQUIRES LEGAL REVIEW.** Both are AGPL service dependencies; isolation is correct but does not eliminate compliance duties.
- **VisDrone: REQUIRES LEGAL REVIEW.** The official dataset repository does not present a clear commercial dataset license. Do not redistribute or train a commercial model until cleared.
- **RTMDet/model weights: REQUIRES LEGAL REVIEW.** MMDetection code is Apache-2.0; weights and training datasets can have separate terms.
- **PostGIS/container distribution: REQUIRES LEGAL REVIEW.** PostGIS is GPL; database-process separation is architecturally clean, but image distribution obligations need counsel.
- **Esri World Imagery: REQUIRES LEGAL REVIEW.** Hosted tile terms and attribution are separate from MapLibre's BSD license.
- PX4, MAVSDK, MapLibre, MMDetection, Raster Vision, TorchGeo, and Open-CD report permissive BSD/MIT/Apache licenses, subject to notice and dependency obligations.

See `THIRD_PARTY_LICENSES.md` for the inventory. No legal conclusion is asserted here.

## Security Risks

- Critical: no authentication, authorization, or organization isolation.
- High: public demo mutation and capture-processing endpoints.
- High: unbounded uploads and full-image memory decoding.
- High: uploaded photogrammetry inputs are not quarantined, scanned, size-limited, or assigned server-generated filenames because an upload layer does not exist yet.
- Medium: no Content Security Policy; MapLibre relies on third-party network imagery.
- Medium: NodeODM task/output retention has no tenant isolation or deletion policy.
- Low: subprocess use employs `execFile` with argument arrays, which avoids shell interpolation, but large-buffer extraction remains unsafe.
- Real-flight safety was improved: a typo or arbitrary `DRONE_MODE` value can no longer enable MAVSDK; two explicit environment switches are required. Production still needs operator confirmation, command authorization, geofencing, and audit logs.

## Geospatial Correctness

The original implementation was not correct for production imagery: it linearly interpolated a WGS84 bounding rectangle, assumed north-up imagery, ignored rotation/skew, and did not inspect the GeoTIFF CRS. This fails for normal projected NodeODM GeoTIFFs and can swap or distort positions.

The revised primitive now:

1. reads all six affine coefficients from the GeoTIFF;
2. requires an explicit source CRS;
3. transforms projected coordinates to EPSG:4326 with `always_xy=True`;
4. returns `(longitude, latitude)` in GeoJSON order;
5. validates WGS84 ranges;
6. applies tile offsets before georeferencing; and
7. runs global class-aware NMS before coordinate conversion.

Unit tests cover northing/easting transformation, rotated affine terms, and duplicate suppression. Still missing are a real NodeODM GeoTIFF fixture, bbox-corner polygon transformation, GCP/accuracy validation, and a PostGIS round-trip test. Therefore the coordinate **primitive appears correct**, but the complete geospatial pipeline is not yet verified.

## MVP Readiness

Verified locally:

- NodeODM HTTP client unit tests with a mocked transport.
- VisDrone annotation conversion.
- Vision tile coverage and class-aware NMS.
- Affine/CRS axis-order primitive with injected transformer.
- Change-comparison alignment guard.
- Real-flight configuration guard.
- Python compilation for repository services.

Not verified or not working end-to-end:

- Web build: dependencies are not installed (`next: command not found`).
- API import/start: Python dependencies are not installed (`fastapi` missing).
- Docker Compose: Docker is not installed on the review host.
- Database creation/migration and PostGIS queries.
- Demo API routes and frontend/API integration.
- Real NodeODM processing, real detector inference, or a GeoTIFF round trip.

## Missing Before Customer Demo

1. Make the frontend consume seeded API data and GeoJSON rather than `lib/demo.ts`.
2. Add a prepared local demo orthomosaic and remove the hard dependency on external Esri tiles.
3. Make `docker compose up` build successfully on a clean machine; add lockfiles and pin images.
4. Implement a minimal retryable processing runner or clearly constrain the demo to preprocessed captures.
5. Add authentication or bind the demo strictly to localhost; disable mutation endpoints outside demo mode.
6. Replace/remove the Ultralytics production dependency pending licensing clearance.

## Missing Before Production

- Tenant-aware authentication/RBAC and audit logging.
- Object storage, validated streaming uploads, malware/file isolation, retention/deletion controls.
- Alembic migrations, backups, restore testing, PostGIS spatial indexes, and PostgreSQL integration tests.
- Durable job execution with idempotency, retries, cancellation, timeouts, and observability.
- Calibrated/validated production model and documented model/data rights.
- Spatial accuracy acceptance tests using known ground control/check points.
- Bounded/vector-tile map delivery for large detection volumes.
- Secure NodeODM tenancy and compute/resource controls.
- Flight-operation safety case before enabling real hardware.

## Recommended Next 5 Engineering Tasks

1. **Unify demo and production reads:** seed PostGIS, add capture-list/metric endpoints, and replace frontend fixtures with the same API/GeoJSON client used for real data.
2. **Make the stack reproducible:** add lockfiles and Alembic migration, pin container versions, bundle a local demo orthomosaic, and prove `docker compose up` plus smoke tests on a clean host.
3. **Implement the minimal capture runner:** persisted stage transitions, a Python NodeODM adapter matching its interface, prepared-orthomosaic bypass, idempotent retries, and terminal error recording.
4. **Complete spatial persistence:** Rasterio windowed reads, affine/CRS bbox-corner transformation, centroid/footprint storage, GiST indexes, and GeoTIFF→PostGIS→GeoJSON integration tests.
5. **Resolve detector and license strategy:** select Apache-2.0 MMDetection/RTMDet or document a commercial Ultralytics license, approve dataset/weight rights, then validate CPU inference and Houston-yard classes.
