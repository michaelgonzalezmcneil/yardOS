from datetime import datetime
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import JSON, CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

JsonType = JSON().with_variant(JSONB, "postgresql")
GeoPoint = Text().with_variant(Geometry("POINT", srid=4326), "postgresql")
GeoShape = Text().with_variant(Geometry("GEOMETRY", srid=4326), "postgresql")


def uid() -> str:
    return str(uuid4())


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(200))


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)


class Site(Base):
    __tablename__ = "sites"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    bounds: Mapped[dict | None] = mapped_column(JsonType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Capture(Base):
    __tablename__ = "captures"
    __table_args__ = (CheckConstraint("status IN ('uploaded','processing','mapping','detecting','analyzing','complete','failed')", name="capture_status_valid"), Index("ix_captures_site_captured_at", "site_id", "captured_at"))
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30), default="uploaded")
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    orthomosaic_url: Mapped[str | None] = mapped_column(Text)
    orthomosaic_crs: Mapped[str | None] = mapped_column(String(120))
    orthomosaic_transform: Mapped[dict | None] = mapped_column(JsonType)
    processing_error: Mapped[str | None] = mapped_column(Text)


class Image(Base):
    __tablename__ = "images"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    capture_id: Mapped[str] = mapped_column(ForeignKey("captures.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JsonType)


class Video(Base):
    __tablename__ = "videos"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    capture_id: Mapped[str] = mapped_column(ForeignKey("captures.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(Text)


class Detection(Base):
    __tablename__ = "detections"
    __table_args__ = (Index("ix_detections_capture_class", "capture_id", "class_name"), Index("ix_detections_capture_timestamp", "capture_id", "timestamp"))
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    capture_id: Mapped[str] = mapped_column(ForeignKey("captures.id", ondelete="CASCADE"), index=True)
    track_id: Mapped[str | None] = mapped_column(ForeignKey("tracks.id", ondelete="SET NULL"), index=True)
    class_name: Mapped[str] = mapped_column(String(80), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    bbox: Mapped[dict] = mapped_column(JsonType)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    geometry: Mapped[str | None] = mapped_column(GeoPoint)
    footprint: Mapped[str | None] = mapped_column(Text().with_variant(Geometry("POLYGON", srid=4326), "postgresql"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    source_image_id: Mapped[str | None] = mapped_column(ForeignKey("images.id", ondelete="SET NULL"), index=True)
    model_version: Mapped[str] = mapped_column(String(120), default="demo-fixture-v1")


class Track(Base):
    __tablename__ = "tracks"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True)
    class_name: Mapped[str] = mapped_column(String(80))
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dwell_seconds: Mapped[float] = mapped_column(Float, default=0)
    distance_moved_m: Mapped[float] = mapped_column(Float, default=0)
    geometry: Mapped[str | None] = mapped_column(Text().with_variant(Geometry("LINESTRING", srid=4326), "postgresql"))


class ChangeEvent(Base):
    __tablename__ = "change_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True)
    before_capture_id: Mapped[str] = mapped_column(ForeignKey("captures.id", ondelete="CASCADE"), index=True)
    after_capture_id: Mapped[str] = mapped_column(ForeignKey("captures.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(40))
    confidence: Mapped[float] = mapped_column(Float)
    geometry: Mapped[str | None] = mapped_column(GeoShape)
    before_image: Mapped[str | None] = mapped_column(Text)
    after_image: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Drone(Base):
    __tablename__ = "drones"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    model: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="offline")


class Mission(Base):
    __tablename__ = "missions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True)
    drone_id: Mapped[str] = mapped_column(ForeignKey("drones.id", ondelete="CASCADE"), index=True)
    state: Mapped[str] = mapped_column(String(40), default="planned")
    planned_path: Mapped[dict | None] = mapped_column(JsonType)
