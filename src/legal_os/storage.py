from __future__ import annotations

import os
from dataclasses import dataclass
from typing import BinaryIO, Protocol, cast

from .settings import Settings, get_settings


class Storage(Protocol):
    def put_object(self, key: str, stream: BinaryIO, length: int) -> None: ...

    def url_for(self, key: str) -> str | None: ...

    def delete_object(self, key: str) -> None: ...

    def exists(self, key: str) -> bool: ...

    def get_object(self, key: str) -> bytes: ...


@dataclass
class LocalStorage:
    base_dir: str

    def _path(self, key: str) -> str:
        return os.path.join(self.base_dir, key)

    def put_object(self, key: str, stream: BinaryIO, length: int) -> None:
        dest_path = self._path(key)
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

    def delete_object(self, key: str) -> None:
        try:
            os.remove(self._path(key))
        except FileNotFoundError:
            pass

    def exists(self, key: str) -> bool:
        return os.path.exists(self._path(key))

    def get_object(self, key: str) -> bytes:
        with open(self._path(key), "rb") as f:
            return f.read()


@dataclass
class MinioStorage:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    secure: bool = True
    url_expires_seconds: int = 900

    def __post_init__(self) -> None:
        try:
            from minio import Minio  # type: ignore
            from minio.error import S3Error  # type: ignore
        except Exception as e:  # pragma: no cover - optional dep
            raise RuntimeError("minio package is required when using MinioStorage") from e
        self._client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )
        self._S3Error = S3Error  # store for use in methods
        # Ensure bucket exists
        if not self._client.bucket_exists(self.bucket):  # pragma: no cover - env dependent
            self._client.make_bucket(self.bucket)

    def put_object(self, key: str, stream: BinaryIO, length: int) -> None:
        self._client.put_object(self.bucket, key, stream, length)

    def url_for(self, key: str) -> str | None:
        try:
            return cast(
                str,
                self._client.presigned_get_object(
                    self.bucket, key, expires=self.url_expires_seconds
                ),
            )
        except Exception:
            return None

    def delete_object(self, key: str) -> None:
        # Best-effort delete
        try:  # pragma: no cover - network dependent
            self._client.remove_object(self.bucket, key)
        except Exception:
            pass

    def exists(self, key: str) -> bool:
        try:  # pragma: no cover - network dependent
            self._client.stat_object(self.bucket, key)
            return True
        except Exception:
            return False

    def get_object(self, key: str) -> bytes:
        try:  # pragma: no cover - network dependent
            resp = self._client.get_object(self.bucket, key)
            try:
                data = resp.read()
                return cast(bytes, data)
            finally:
                resp.close()
                resp.release_conn()
        except Exception as e:
            raise FileNotFoundError(key) from e


def document_original_key(document_id: str, version_id: str) -> str:
    return f"documents/{document_id}/{version_id}/original.pdf"


def artifact_key(document_id: str, version_id: str, name: str) -> str:
    return f"documents/{document_id}/{version_id}/artifacts/{name}"


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
            url_expires_seconds=s.minio_url_expires_seconds,
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
            url_expires_seconds=s.minio_url_expires_seconds,
        )
    os.makedirs(s.uploads_dir, exist_ok=True)
    return LocalStorage(base_dir=s.uploads_dir)
