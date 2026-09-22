from __future__ import annotations

import shutil
from pathlib import Path
from typing import BinaryIO, Protocol


def artifact_uri(site_id: str, capture_id: str, category: str, filename: str, bucket: str = "yardos") -> str:
    safe = (site_id, capture_id, category, filename)
    if any(not value or value.startswith("/") or ".." in Path(value).parts for value in safe):
        raise ValueError("Artifact path components must be non-empty relative paths")
    return f"s3://{bucket}/sites/{site_id}/captures/{capture_id}/{category}/{filename}"


class ArtifactStore(Protocol):
    def put_file(self, source: str | Path, uri: str) -> str: ...
    def open(self, uri: str) -> BinaryIO: ...
    def exists(self, uri: str) -> bool: ...


class LocalArtifactStore:
    """S3-shaped local adapter for tests and offline development."""

    def __init__(self, root: str | Path = "data/object-store"):
        self.root = Path(root)

    def _path(self, uri: str) -> Path:
        if not uri.startswith("s3://"):
            raise ValueError(f"Unsupported artifact URI: {uri}")
        bucket_and_key = uri.removeprefix("s3://")
        if ".." in Path(bucket_and_key).parts:
            raise ValueError("Artifact URI may not traverse directories")
        return self.root / bucket_and_key

    def put_file(self, source: str | Path, uri: str) -> str:
        target = self._path(uri)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        return uri

    def open(self, uri: str) -> BinaryIO:
        return self._path(uri).open("rb")

    def exists(self, uri: str) -> bool:
        return self._path(uri).exists()


class MinioArtifactStore:
    """Thin S3 adapter; imports boto3 only when selected."""

    def __init__(self, endpoint_url: str, access_key: str, secret_key: str):
        try:
            import boto3
        except ImportError as error:
            raise RuntimeError("Install boto3 to use STORAGE_PROVIDER=minio") from error
        self.client = boto3.client("s3", endpoint_url=endpoint_url, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    @staticmethod
    def _parts(uri: str) -> tuple[str, str]:
        if not uri.startswith("s3://"):
            raise ValueError(f"Unsupported artifact URI: {uri}")
        return tuple(uri.removeprefix("s3://").split("/", 1))  # type: ignore[return-value]

    def put_file(self, source: str | Path, uri: str) -> str:
        bucket, key = self._parts(uri)
        self.client.upload_file(str(source), bucket, key)
        return uri

    def open(self, uri: str) -> BinaryIO:
        bucket, key = self._parts(uri)
        return self.client.get_object(Bucket=bucket, Key=key)["Body"]

    def exists(self, uri: str) -> bool:
        bucket, key = self._parts(uri)
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except self.client.exceptions.ClientError:
            return False
