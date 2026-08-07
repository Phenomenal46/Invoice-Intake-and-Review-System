from __future__ import annotations

import hashlib
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx
from fastapi import HTTPException, UploadFile

from app.config import settings


# This helper keeps the upload flow in one place so development can use disk and production can use Cloudinary.
@dataclass(slots=True)
class StoredUpload:
    file_url: str
    local_path: str
    cleanup_path: Path | None = None
    filename: str | None = None
    mime_type: str | None = None


def _build_unique_filename(filename: str | None) -> str:
    suffix = Path(filename or "").suffix
    return f"{uuid.uuid4()}{suffix}"


def _copy_upload(upload_file: UploadFile, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    upload_file.file.seek(0)
    with destination.open("wb") as output_file:
        shutil.copyfileobj(upload_file.file, output_file)


def _save_temp_upload(upload_file: UploadFile) -> Path:
    suffix = Path(upload_file.filename or "").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        upload_file.file.seek(0)
        shutil.copyfileobj(upload_file.file, temp_file)
        return Path(temp_file.name)


def _cloudinary_signature(timestamp: str) -> str:
    if not settings.cloudinary_api_secret:
        raise HTTPException(status_code=500, detail="Cloudinary is missing its API secret.")

    signature_source = f"timestamp={timestamp}{settings.cloudinary_api_secret}"
    return hashlib.sha1(signature_source.encode("utf-8")).hexdigest()


def _upload_to_cloudinary(upload_file: UploadFile, local_path: Path) -> str:
    if not settings.cloudinary_cloud_name or not settings.cloudinary_api_key:
        raise HTTPException(status_code=500, detail="Cloudinary is missing its credentials.")

    timestamp = str(int(time.time()))
    payload = {
        "timestamp": timestamp,
        "api_key": settings.cloudinary_api_key,
        "signature": _cloudinary_signature(timestamp),
    }

    upload_url = f"https://api.cloudinary.com/v1_1/{settings.cloudinary_cloud_name}/auto/upload"
    with local_path.open("rb") as file_handle:
        response = httpx.post(
            upload_url,
            data=payload,
            files={"file": (upload_file.filename or local_path.name, file_handle, upload_file.content_type or "application/octet-stream")},
            timeout=60.0,
        )

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail="Cloudinary upload failed.") from exc

    body = response.json()
    secure_url = body.get("secure_url")
    if not secure_url:
        raise HTTPException(status_code=502, detail="Cloudinary did not return a file URL.")

    return secure_url


def store_upload(upload_file: UploadFile, request_base_url: str) -> StoredUpload:
    if settings.use_cloudinary_storage:
        temp_path = _save_temp_upload(upload_file)
        try:
            file_url = _upload_to_cloudinary(upload_file, temp_path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

        return StoredUpload(
            file_url=file_url,
            local_path=str(temp_path),
            cleanup_path=temp_path,
            filename=upload_file.filename,
            mime_type=upload_file.content_type,
        )

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = _build_unique_filename(upload_file.filename)
    local_path = upload_dir / filename
    _copy_upload(upload_file, local_path)

    file_url = f"{request_base_url.rstrip('/')}/uploads/{filename}"
    return StoredUpload(
        file_url=file_url,
        local_path=str(local_path),
        cleanup_path=None,
        filename=upload_file.filename,
        mime_type=upload_file.content_type,
    )