# YardOS aerial processing pipeline

This repository connects two isolated services: [NodeODM](https://github.com/OpenDroneMap/NodeODM) creates geospatial outputs from drone imagery, then a FastAPI/Ultralytics service detects aerial objects in the resulting orthophoto. The detection code is original YardOS integration code; no third-party repository is vendored.

## Documentation map

- Start here: [`docs/README.md`](./docs/README.md)
- Canonical architecture: [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- System boundary and processing stages: [`docs/SYSTEM_ARCHITECTURE.md`](./docs/SYSTEM_ARCHITECTURE.md)
- Provider interfaces and adapter boundaries: [`docs/PROVIDERS.md`](./docs/PROVIDERS.md)
- Dependency direction: [`docs/DEPENDENCY_GRAPH.md`](./docs/DEPENDENCY_GRAPH.md)

## Prerequisites

- Docker Desktop (allocate at least 4 GB RAM; 8+ GB is better for real datasets)
- Node.js 20 or newer and Python 3.11+
- `unzip` (preinstalled on macOS and most Linux distributions)
- A set of overlapping, geotagged aerial JPG/TIFF images. A useful reconstruction generally needs substantially more than two images.

## Start NodeODM

The fastest supported setup uses OpenDroneMap's official image:

```bash
cp .env.example .env
docker compose up -d nodeodm
docker compose logs -f nodeodm
```

When the service is ready, verify it:

```bash
curl http://127.0.0.1:3000/info
```

Processing data is persisted under `data/nodeodm/` and is ignored by Git. Stop the service with `docker compose down`. Do not use `down -v` if you want to retain NodeODM tasks.

### Optional official source checkout

The Docker image is the recommended runtime and requires no source changes. To inspect or build the exact upstream service locally, clone the official repository into the ignored service directory:

```bash
mkdir -p services
git clone --depth 1 https://github.com/OpenDroneMap/NodeODM.git services/NodeODM
```

The YardOS client does not import from or modify that checkout. On this development machine the clone could not complete because the disk had only ~124 MB free; the official Docker image remains the configured runtime.

## Configuration

Copy `.env.example` to `.env`, then export the values before running scripts (Node does not automatically load dotenv files):

```bash
set -a
source .env
set +a
```

| Variable | Default | Purpose |
| --- | --- | --- |
| `NODEODM_HOST` | `127.0.0.1` | NodeODM hostname |
| `NODEODM_PORT` | `3000` | Published NodeODM port |
| `NODEODM_PROTOCOL` | `http` | Protocol used by the client |
| `NODEODM_POLL_INTERVAL_MS` | `5000` | Status polling interval |
| `NODEODM_OUTPUT_DIR` | `./data/nodeodm-results` | Downloaded task results |

## Process a test scan

Start NodeODM, load the environment, and pass either one folder or a list of image files:

```bash
npm run process-test-scan -- ./sample-images
# or
npm run process-test-scan -- ./images/DJI_0001.JPG ./images/DJI_0002.JPG ./images/DJI_0003.JPG
```

The script performs the complete flow:

1. `POST /task/new` with the images as multipart form data.
2. Poll `GET /task/:uuid/info` until status `40` (completed).
3. Download `GET /task/:uuid/download/all.zip`.
4. Extract `odm_orthophoto/odm_orthophoto.tif` to `data/nodeodm-results/<task-id>/orthophoto.tif`.

Photogrammetry can take minutes or hours depending on the image count, resolution, and available CPU/RAM. The script deliberately has no default timeout.

## Use from YardOS code

```js
import { NodeOdmClient } from "./src/services/nodeodm.js";

const nodeOdm = new NodeOdmClient();
const result = await nodeOdm.processScan("./incoming/scan-2026-09-22", {
  outputDirectory: "./data/nodeodm-results",
  options: { "orthophoto-resolution": 5 },
  onProgress: ({ progress }) => console.log(`${progress}%`),
});

console.log(result.orthophotoPath);
```

For a web request, enqueue `processScan` in a background worker rather than keeping an HTTP request open for the entire reconstruction.

## Checks

```bash
npm run check
npm test
docker compose config
```

The automated tests use mocked service transports and do not require Docker, model weights, or a real photogrammetry run.

## Brighton Beach real-data integration

The opt-in integration fixture is [`pierotofy/drone_dataset_brighton_beach`](https://github.com/pierotofy/drone_dataset_brighton_beach). Its repository currently contains 18 original JPGs under `images/` (`DJI_0018.JPG` through `DJI_0035.JPG`) plus reference outputs. The ODMdata catalog describes the set as 18 EXIF-geotagged images without GCP or RTK. The repository declares BSD-2-Clause, but its license does not separately enumerate the photographs; YardOS therefore downloads it locally, never commits or redistributes it, and does not claim broader commercial imagery rights.

Fetch and validate the source set:

```bash
python scripts/brighton_beach_integration.py fetch
python scripts/brighton_beach_integration.py validate
```

Validation opens every image, requires at least three distinct GPS positions, reports actual versus expected image count and dimensions, and requires GPS EXIF on every input. Successful reconstruction is the definitive overlap check; the validator does not invent or claim an overlap percentage.

Install the API dependencies, start the real services, and run the complete integration:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt -r services/vision/requirements.txt

cp .env.example .env
# Set VISION_PROVIDER=yolo. A mock vision response is rejected by this command.
docker compose --profile photogrammetry --profile vision up -d nodeodm vision db

set -a; source .env; set +a
DATABASE_URL=sqlite:///./data/integration-results/brighton.db \
  python scripts/brighton_beach_integration.py run
```

The run is retry-safe at the worker boundary: once NodeODM returns a task UUID it is persisted on the processing job and reused. It downloads the task archive, reads the real orthophoto GeoTIFF CRS and six-value GDAL affine transform, rejects absent/identity georeferencing, transforms detection centers to EPSG:4326 with `pyproj`, and persists the capture artifacts and detections. Zero relevant vehicles is a valid successful result. Output and the JSON integration report remain under ignored `data/integration-results/`.

Serve the resulting capture in the map:

```bash
export DATABASE_URL=sqlite:///./data/integration-results/brighton.db
uvicorn apps.api.app.main:app --port 8000
export NEXT_PUBLIC_API_URL=http://localhost:8000
export NEXT_PUBLIC_CAPTURE_ID=<capture_id-from-report>
npm --prefix apps/web run dev
```

The map now loads `/captures/<capture-id>/detections.geojson`; it no longer renders `apps/web/lib/demo.ts`. Inspect the persisted geospatial artifact with `GET /captures/<capture-id>/artifacts` and the job/task state with `GET /processing/jobs/<job-id>`.

## Mock API processing pipeline

The API can exercise the YardOS-owned processing DAG without Docker, imagery, or model weights. Mock providers still produce canonical artifacts and georeferenced detections, and the SQLAlchemy repository persists the results.

```bash
curl -X POST http://127.0.0.1:8000/captures/<capture-id>/process \
  -H 'content-type: application/json' \
  -d '{"image_urls":["mock://DJI_0001.JPG"]}'
```

The response is `202 Accepted` and includes a `job_id`. Inspect it with:

```bash
curl http://127.0.0.1:8000/processing/jobs/<job-id>
curl http://127.0.0.1:8000/captures/<capture-id>/detections
```

When `DEMO_MODE=true`, omitting `image_urls` uses a synthetic mock image URI. No fake pixels are analyzed: the deterministic provider exists to verify orchestration, persistence, API behavior, and the frontend contract. Set `DEMO_MODE=false` to require stored or explicitly supplied images.

## Aerial vision service

The service lives in `services/vision`. It provides:

- `YOLODetectionProvider`, backed by an Ultralytics pretrained or fine-tuned checkpoint.
- `MockDetectionProvider`, a deterministic fallback for demos without weights or a GPU.
- 1024×1024 overlapping orthomosaic tiles, global-coordinate restoration, and class-aware NMS.
- `POST /detect` for JPG, PNG, and NodeODM GeoTIFF inputs.

Start NodeODM and vision together:

```bash
cp .env.example .env
docker compose up --build -d nodeodm vision
curl http://127.0.0.1:8000/health
```

The default provider is `mock`, so the demo starts without downloading a model. To use YOLO's pretrained COCO vehicle classes, set these in `.env` and restart:

```bash
VISION_PROVIDER=yolo
VISION_MODEL_PATH=yolo11n.pt
VISION_MODEL_VERSION=yolo11n-coco
```

The named pretrained weight is downloaded by Ultralytics on first use and is not committed. A VisDrone-fine-tuned checkpoint should instead be copied to `services/vision/models/` and referenced as `/app/models/best.pt` inside Docker. COCO provides `car`, `truck`, and `bus`; train on the prepared VisDrone subset to add `van` as its own class.

Test inference:

```bash
curl -X POST http://127.0.0.1:8000/detect \
  -F 'file=@/absolute/path/to/aerial-image.jpg'
```

The response includes pixel bounding boxes and centers in the original image coordinate system, plus image dimensions, model version, inference time, and whether tiling was used.

## VisDrone bootstrap dataset

Download the official **Task 1: Object Detection in Images** train and validation archives from the [VisDrone dataset repository](https://github.com/VisDrone/VisDrone-Dataset). Extract them without renaming:

```text
services/vision/training/datasets/raw/
  VisDrone2019-DET-train/
    images/
    annotations/
  VisDrone2019-DET-val/
    images/
    annotations/
```

The data is intentionally ignored by Git. VisDrone labels IDs 4, 5, 6, and 9 as car, van, truck, and bus. The converter retains only those genuine classes and converts `[left, top, width, height]` annotations to normalized YOLO labels:

```bash
cd services/vision
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python training/prepare_visdrone.py
```

Paths can be overridden with `VISDRONE_RAW_DIR` and `VISION_DATASETS_DIR`, or via `--raw-dir` and `--output-dir`.

## Fine-tuning and evaluation

Fine-tune from pretrained weights rather than training from scratch:

```bash
cd services/vision
source .venv/bin/activate
python training/train.py --model yolo11n.pt --epochs 50 --imgsz 1024
python training/evaluate.py --model runs/yardos/aerial-bootstrap/weights/best.pt
```

Training paths and parameters can also be set with `VISION_DATASETS_DIR`, `VISION_TRAIN_MODEL`, `VISION_EPOCHS`, `VISION_IMAGE_SIZE`, and `VISION_DEVICE`.

## Adding Houston yard classes

The placeholder at `services/vision/training/datasets/yardos/` documents the YOLO layout. Its separate class configuration is:

1. `trailer`
2. `shipping_container`
3. `tractor`
4. `chassis`
5. `heavy_equipment`
6. `car`

Place locally labeled images under `images/train` and `images/val`, with matching normalized YOLO text files under `labels/train` and `labels/val`. Copy `training/yardos.dataset.example.yaml` to the dataset root and update its path. Do not relabel these categories as VisDrone classes; VisDrone is only the aerial visual bootstrap.

## Complete NodeODM → detection flow

With both services running, the existing command now performs the whole pipeline and persists a structured detection record:

```bash
set -a; source .env; set +a
npm run process-test-scan -- ./sample-images
```

Outputs are written to:

```text
data/nodeodm-results/<scan-id>/orthophoto.tif
data/vision/<scan-id>-detections.json
```

Each detection record stores `scan_id`, `asset_class`, `confidence`, bounding box, center coordinates, and `model_version`. This JSON store is the current repository's persistence adapter; it can be replaced by the YardOS database when that schema exists. Use `--skip-vision` to run only photogrammetry.

## Vision-only checks

```bash
npm run check
npm test

# With Python dependencies installed:
cd services/vision
ruff check app training tests
pytest -q
```
