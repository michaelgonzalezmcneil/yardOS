from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    photogrammetry_provider: str = "mock"
    detector_provider: str = "mock"
    segmentation_provider: str = "mock"
    change_provider: str = "simple"
    tracking_provider: str = "simple"
    storage_provider: str = "local"
    storage_bucket: str = "yardos"
    storage_local_root: str = "data/object-store"
    s3_endpoint_url: str = "http://127.0.0.1:9000"
    s3_access_key: str = "yardos"
    s3_secret_key: str = "yardos-local"
    nodeodm_host: str = "127.0.0.1"
    nodeodm_port: int = 3000

    @classmethod
    def from_env(cls) -> "Settings":
        def value(name: str, default: str) -> str:
            return os.getenv(name, default)

        return cls(
            photogrammetry_provider=value("PHOTOGRAMMETRY_PROVIDER", "mock"),
            detector_provider=value("DETECTOR_PROVIDER", "mock"),
            segmentation_provider=value("SEGMENTATION_PROVIDER", "mock"),
            change_provider=value("CHANGE_PROVIDER", "simple"),
            tracking_provider=value("TRACKING_PROVIDER", "simple"),
            storage_provider=value("STORAGE_PROVIDER", "local"),
            storage_bucket=value("STORAGE_BUCKET", "yardos"),
            storage_local_root=value("STORAGE_LOCAL_ROOT", "data/object-store"),
            s3_endpoint_url=value("S3_ENDPOINT_URL", "http://127.0.0.1:9000"),
            s3_access_key=value("S3_ACCESS_KEY", "yardos"),
            s3_secret_key=value("S3_SECRET_KEY", "yardos-local"),
            nodeodm_host=value("NODEODM_HOST", "127.0.0.1"),
            nodeodm_port=int(value("NODEODM_PORT", "3000")),
        )
