from contextlib import asynccontextmanager
import os

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .demo import FRIDAY_ID, SITE_ID, load_demo
from packages.contracts import Capture as ContractCapture
from packages.contracts import ProcessingJob as ContractJob

from .models import Capture, ChangeEvent, Detection, Image, MappingArtifact, ProcessingArtifact, ProcessingJob, Site, Track
from .repository import SqlAlchemyRepository
from .runtime import run_capture_job
from .schemas import CaptureCreate, CaptureRead, DetectionRead, MappingArtifactRead, ProcessRequest, ProcessResponse, ProcessingArtifactRead, ProcessingJobRead, SiteCreate, SiteRead


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        load_demo(db)
    yield


app = FastAPI(title="YardOS API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "mode": "demo"}


@app.post("/demo/load")
def demo_load(db: Session = Depends(get_db)):
    return load_demo(db)


@app.post("/sites", response_model=SiteRead)
def create_site(payload: SiteCreate, db: Session = Depends(get_db)):
    site = Site(**payload.model_dump())
    db.add(site); db.commit(); db.refresh(site)
    return site


@app.get("/sites", response_model=list[SiteRead])
def list_sites(db: Session = Depends(get_db)):
    return list(db.scalars(select(Site).order_by(Site.created_at.desc())))


@app.get("/sites/{site_id}", response_model=SiteRead)
def get_site(site_id: str, db: Session = Depends(get_db)):
    site = db.get(Site, site_id)
    if not site: raise HTTPException(404, "Site not found")
    return site


@app.post("/captures", response_model=CaptureRead)
def create_capture(payload: CaptureCreate, db: Session = Depends(get_db)):
    if not db.get(Site, payload.site_id): raise HTTPException(404, "Site not found")
    capture = Capture(**payload.model_dump(), status="uploaded")
    db.add(capture); db.commit(); db.refresh(capture)
    return capture


@app.get("/captures/{capture_id}", response_model=CaptureRead)
def get_capture(capture_id: str, db: Session = Depends(get_db)):
    capture = db.get(Capture, capture_id)
    if not capture: raise HTTPException(404, "Capture not found")
    return capture


@app.post("/captures/{capture_id}/process", response_model=ProcessResponse, status_code=202)
def process_capture(capture_id: str, background_tasks: BackgroundTasks, payload: ProcessRequest | None = None, db: Session = Depends(get_db)):
    capture = db.get(Capture, capture_id)
    if not capture: raise HTTPException(404, "Capture not found")
    active = db.scalar(select(ProcessingJob).where(ProcessingJob.capture_id == capture_id, ProcessingJob.state.in_(["queued", "running"])).order_by(ProcessingJob.created_at.desc()))
    if active:
        return ProcessResponse(job_id=active.id, capture_id=capture_id, status=active.state, message=f"Existing job is at {active.current_step}")

    supplied_urls = payload.image_urls if payload else []
    stored_urls = list(db.scalars(select(Image.url).where(Image.capture_id == capture_id)))
    image_urls = supplied_urls or stored_urls
    if not image_urls and os.getenv("DEMO_MODE", "true").lower() == "true":
        image_urls = [f"mock://captures/{capture_id}/DJI_0001.JPG"]
    if not image_urls:
        raise HTTPException(400, "Capture has no images; upload images or pass image_urls")

    contract_capture = ContractCapture(site_id=capture.site_id, label=capture.label, id=capture.id, captured_at=capture.captured_at, metadata={"source": "api"})
    contract_job = ContractJob(capture_id=capture.id)
    SqlAlchemyRepository(db).save_job(contract_job)
    background_tasks.add_task(run_capture_job, contract_capture, image_urls, contract_job)
    return ProcessResponse(job_id=contract_job.id, capture_id=capture_id, status="queued", message="Queued: metadata → mapping → detection + segmentation → georeference → persistence")


@app.get("/processing/jobs/{job_id}", response_model=ProcessingJobRead)
def get_processing_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(ProcessingJob, job_id)
    if not job:
        raise HTTPException(404, "Processing job not found")
    artifacts = db.execute(select(ProcessingArtifact.artifact_id, ProcessingArtifact.role).where(ProcessingArtifact.job_id == job_id)).all()
    return ProcessingJobRead(
        id=job.id,
        capture_id=job.capture_id,
        state=job.state,
        current_step=job.current_step,
        error=job.error,
        provider_task_id=(job.metadata_json or {}).get("provider_task_id"),
        created_at=job.created_at,
        updated_at=job.updated_at,
        artifacts=[ProcessingArtifactRead(artifact_id=artifact_id, role=role) for artifact_id, role in artifacts],
    )


@app.get("/captures/{capture_id}/artifacts", response_model=list[MappingArtifactRead])
def capture_artifacts(capture_id: str, db: Session = Depends(get_db)):
    if not db.get(Capture, capture_id):
        raise HTTPException(404, "Capture not found")
    return list(db.scalars(select(MappingArtifact).where(MappingArtifact.capture_id == capture_id)))


@app.get("/captures/{capture_id}/detections", response_model=list[DetectionRead])
def capture_detections(capture_id: str, db: Session = Depends(get_db)):
    return list(db.scalars(select(Detection).where(Detection.capture_id == capture_id)))


@app.get("/captures/{capture_id}/detections.geojson")
def detections_geojson(capture_id: str, db: Session = Depends(get_db)):
    detections = db.scalars(select(Detection).where(Detection.capture_id == capture_id))
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "id": item.id, "geometry": {"type": "Point", "coordinates": [item.longitude, item.latitude]}, "properties": {"id": item.id, "class_name": item.class_name, "confidence": item.confidence, "bbox": item.bbox, "timestamp": item.timestamp.isoformat(), "source_image_id": item.source_image_id, "source_artifact_id": item.source_artifact_id, "model_name": item.model_name, "model_version": item.model_version, "is_mock": "mock" in (item.model_version or "").lower()}} for item in detections]}


@app.get("/sites/{site_id}/changes")
def site_changes(site_id: str, db: Session = Depends(get_db)):
    rows = db.scalars(select(ChangeEvent).where(ChangeEvent.site_id == site_id))
    return [{"id": row.id, "type": row.type, "confidence": row.confidence, "before_image": row.before_image, "after_image": row.after_image} for row in rows]


@app.get("/sites/{site_id}/tracks")
def site_tracks(site_id: str, db: Session = Depends(get_db)):
    return list(db.scalars(select(Track).where(Track.site_id == site_id)))


@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Detection.class_name, func.count()).where(Detection.capture_id == FRIDAY_ID).group_by(Detection.class_name)).all())
    return {"site_id": SITE_ID, "capture_id": FRIDAY_ID, "counts": counts, "changes": db.scalar(select(func.count()).select_from(ChangeEvent).where(ChangeEvent.site_id == SITE_ID))}
