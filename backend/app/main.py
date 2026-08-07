from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# IMPORT StaticFiles: This acts like a mini web-server just for files
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config import settings

app = FastAPI(title=settings.app_name)

# The upload folder must be created from an absolute path so Windows, Linux, and Render all use the same location.
upload_dir = Path(settings.upload_dir)
upload_dir.mkdir(parents=True, exist_ok=True)

# MOUNT the folder: This tells the server, "If a URL starts with /uploads, look in the uploads folder!"
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

app.add_middleware(
	CORSMiddleware,
	allow_origins=settings.parsed_cors_origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
