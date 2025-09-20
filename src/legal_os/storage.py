from __future__ import annotations

import os
from dataclasses import dataclass
from typing import BinaryIO, Protocol

from .settings import Settings, get_settings


class Storage(Protocol):
    def put_object(self, key: str, stream: BinaryIO, length: int) -> None: ...

    def url_for(self, key: str) -> str | None: ...


@dataclass
class LocalStorage:
    base_dir: str

    def put_object(self, key: str, stream: BinaryIO, length: int) -> None:
        dest_path = os.path.join(self.base_dir, key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            remaining = length
            while remaining > 0:
                chunk = stream.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)

    def url_for(self, key: str) -> str | None:
        return None


@dataclass
class MinioStorage:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    secure: bool = True

    def __post_init__(self) -> None:
        try:
            from minio import Minio  # type: ignore
        except Exception as e:  # pragma: no cover - optional dep
            raise RuntimeError("minio package is required when using MinioStorage") from e
        self._client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )
        # Ensure bucket exists
        if not self._client.bucket_exists(self.bucket):  # pragma: no cover - environment dependent
            self._client.make_bucket(self.bucket)

    def put_object(self, key: str, stream: BinaryIO, length: int) -> None:
        self._client.put_object(self.bucket, key, stream, length)

    def url_for(self, key: str) -> str | None:
        # Could generate a presigned URL; keeping simple for now
        return None


def get_storage() -> Storage:
    s = get_settings()
    if (
        s.flags.enable_minio
        and s.minio_endpoint
        and s.minio_access_key
        and s.minio_secret_key
        and s.minio_bucket
    ):
        return MinioStorage(
            endpoint=s.minio_endpoint,
            access_key=s.minio_access_key,
            secret_key=s.minio_secret_key,
            bucket=s.minio_bucket,
            secure=s.minio_secure,
        )
    os.makedirs(s.uploads_dir, exist_ok=True)
    return LocalStorage(base_dir=s.uploads_dir)


def get_storage_from_settings(s: Settings) -> Storage:
    if (
        s.flags.enable_minio
        and s.minio_endpoint
        and s.minio_access_key
        and s.minio_secret_key
        and s.minio_bucket
    ):
        return MinioStorage(
            endpoint=s.minio_endpoint,
            access_key=s.minio_access_key,
            secret_key=s.minio_secret_key,
            bucket=s.minio_bucket,
            secure=s.minio_secure,
        )
    os.makedirs(s.uploads_dir, exist_ok=True)
    return LocalStorage(base_dir=s.uploads_dir)
