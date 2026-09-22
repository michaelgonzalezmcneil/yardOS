from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .demo import FRIDAY_ID, SITE_ID, load_demo
from .models import Capture, ChangeEvent, Detection, Site, Track
from .schemas import CaptureCreate, CaptureRead, DetectionRead, ProcessResponse, SiteCreate, SiteRead


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


@app.post("/captures/{capture_id}/process", response_model=ProcessResponse)
def process_capture(capture_id: str, db: Session = Depends(get_db)):
    capture = db.get(Capture, capture_id)
    if not capture: raise HTTPException(404, "Capture not found")
    capture.status = "processing"; db.commit()
    return ProcessResponse(capture_id=capture_id, status="processing", message="Queued: metadata → mapping → detection → analysis")


@app.get("/captures/{capture_id}/detections", response_model=list[DetectionRead])
def capture_detections(capture_id: str, db: Session = Depends(get_db)):
    return list(db.scalars(select(Detection).where(Detection.capture_id == capture_id)))


@app.get("/captures/{capture_id}/detections.geojson")
def detections_geojson(capture_id: str, db: Session = Depends(get_db)):
    detections = db.scalars(select(Detection).where(Detection.capture_id == capture_id))
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "id": item.id, "geometry": {"type": "Point", "coordinates": [item.longitude, item.latitude]}, "properties": {"id": item.id, "class_name": item.class_name, "confidence": item.confidence, "bbox": item.bbox, "timestamp": item.timestamp.isoformat(), "source_image_id": item.source_image_id, "model_version": item.model_version}} for item in detections]}


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
