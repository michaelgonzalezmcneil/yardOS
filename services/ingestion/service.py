from __future__ import annotations

from pathlib import Path
from typing import Sequence

from packages.contracts import Capture


class MetadataExtractor:
    def extract(self, image_uris: Sequence[str]) -> dict:
        suffixes = sorted({Path(uri).suffix.lower() for uri in image_uris})
        return {"image_count": len(image_uris), "extensions": suffixes}


class CaptureValidator:
    def validate(self, capture: Capture, image_uris: Sequence[str]) -> None:
        if not capture.site_id:
            raise ValueError("Capture must belong to a site")
        if not image_uris:
            raise ValueError("Capture must contain at least one image")
        unsupported = [uri for uri in image_uris if Path(uri).suffix.lower() not in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}]
        if unsupported:
            raise ValueError(f"Unsupported image type: {unsupported[0]}")
