from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile

from app.config import settings


# Cloudinary is configured from environment variables so production can swap in real credentials safely.
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


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


def _build_cloudinary_public_id(filename: str | None) -> str:
    # Keep Cloudinary public IDs clean so PDF URLs do not become malformed like .pdf.pdf.
    stem = Path(filename or "").stem or uuid.uuid4().hex
    return f"document-workflow/{uuid.uuid4().hex}-{stem}"


def _upload_to_cloudinary(upload_file: UploadFile, local_path: Path) -> str:
    if not settings.cloudinary_cloud_name or not settings.cloudinary_api_key or not settings.cloudinary_api_secret:
        raise HTTPException(status_code=500, detail="Cloudinary is missing its credentials.")

    public_id = _build_cloudinary_public_id(upload_file.filename)
    suffix = (Path(upload_file.filename or "").suffix or "").lower()
    resource_type = "raw" if suffix == ".pdf" else "auto"

    try:
        upload_result = cloudinary.uploader.upload(
            str(local_path),
            public_id=public_id,
            resource_type=resource_type,
            type="upload",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="Cloudinary upload failed.") from exc

    secure_url = upload_result.get("secure_url") or upload_result.get("url")
    if not secure_url:
        raise HTTPException(status_code=502, detail="Cloudinary did not return a file URL.")

    return secure_url


def store_upload(upload_file: UploadFile, request_base_url: str) -> StoredUpload:
    if settings.use_cloudinary_storage:
        # Cloudinary needs a real file path here because Gemini also reads the same temporary file.
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

    # Local mode keeps the file on disk and serves it through FastAPI's static mount.
    file_url = f"{request_base_url.rstrip('/')}/uploads/{filename}"
    return StoredUpload(
        file_url=file_url,
        local_path=str(local_path),
        cleanup_path=None,
        filename=upload_file.filename,
        mime_type=upload_file.content_type,
    )