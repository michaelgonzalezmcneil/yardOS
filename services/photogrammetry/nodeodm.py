from __future__ import annotations

import json
import time
import zipfile
from pathlib import Path
from typing import Any, Callable, Sequence

def _httpx():
    try:
        import httpx
    except ImportError as error:
        raise RuntimeError("Install the API dependencies to use PHOTOGRAMMETRY_PROVIDER=nodeodm") from error
    return httpx


class NodeODMError(RuntimeError):
    pass


class NodeODMClient:
    """Small, synchronous client for the NodeODM HTTP API."""

    def __init__(self, host: str = "localhost", port: int = 3000, *, timeout: float = 120.0):
        scheme = "http://" if "://" not in host else ""
        self.base_url = f"{scheme}{host.rstrip('/')}:{port}" if scheme else f"{host.rstrip('/')}:{port}"
        self.timeout = timeout

    def create_task(self, image_paths: Sequence[str], *, options: dict[str, Any] | None = None) -> str:
        paths = [Path(value).expanduser().resolve() for value in image_paths]
        missing = [str(path) for path in paths if not path.is_file()]
        if missing:
            raise NodeODMError(f"NodeODM input files do not exist: {missing}")
        handles = [path.open("rb") for path in paths]
        try:
            files = [("images", (path.name, handle, "image/jpeg")) for path, handle in zip(paths, handles)]
            data = {"options": json.dumps(options or {})}
            response = _httpx().post(f"{self.base_url}/task/new", files=files, data=data, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        finally:
            for handle in handles:
                handle.close()
        task_id = payload.get("uuid")
        if not task_id:
            raise NodeODMError(f"NodeODM did not return a task UUID: {payload}")
        return str(task_id)

    def get_task(self, task_id: str) -> dict[str, Any]:
        response = _httpx().get(f"{self.base_url}/task/{task_id}/info", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def download_artifacts(self, task_id: str, output_dir: str | Path) -> dict[str, str]:
        destination = Path(output_dir).expanduser().resolve() / task_id
        destination.mkdir(parents=True, exist_ok=True)
        archive = destination / "all.zip"
        with _httpx().stream("GET", f"{self.base_url}/task/{task_id}/download/all.zip", timeout=None) as response:
            response.raise_for_status()
            with archive.open("wb") as target:
                for chunk in response.iter_bytes():
                    target.write(chunk)
        with zipfile.ZipFile(archive) as package:
            for member in package.infolist():
                resolved = (destination / member.filename).resolve()
                if destination not in resolved.parents and resolved != destination:
                    raise NodeODMError(f"Unsafe path in NodeODM archive: {member.filename}")
            package.extractall(destination)
        candidates = {
            "orthomosaic": ["odm_orthophoto/odm_orthophoto.tif"],
            "point_cloud": ["odm_georeferencing/odm_georeferenced_model.laz", "odm_georeferencing/odm_georeferenced_model.ply"],
            "dem": ["odm_dem/dsm.tif", "odm_dem/dtm.tif"],
        }
        found: dict[str, str] = {}
        for name, relative_paths in candidates.items():
            for relative in relative_paths:
                matches = list(destination.rglob(Path(relative).name))
                if matches:
                    found[name] = str(matches[0])
                    break
        if "orthomosaic" not in found:
            raise NodeODMError(f"Task {task_id} archive contains no odm_orthophoto.tif")
        return found

    def wait(self, task_id: str, *, poll_seconds: float = 5, timeout_seconds: float = 14400, on_status: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            info = self.get_task(task_id)
            if on_status:
                on_status(info)
            status = info.get("status", {})
            code = int(status.get("code", status if isinstance(status, int) else -1))
            if code == 40:
                return info
            if code in {30, 50}:
                raise NodeODMError(f"NodeODM task {task_id} failed: {info.get('error') or status}")
            time.sleep(poll_seconds)
        raise TimeoutError(f"NodeODM task {task_id} exceeded {timeout_seconds} seconds")
