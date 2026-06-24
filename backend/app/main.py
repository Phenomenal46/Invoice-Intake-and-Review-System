import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# IMPORT StaticFiles: This acts like a mini web-server just for files
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config import settings

app = FastAPI(title=settings.app_name)

# Ensure the uploads directory exists just in case we forgot to make it
os.makedirs("uploads", exist_ok=True)

# MOUNT the folder: This tells the server, "If a URL starts with /uploads, look in the uploads folder!"
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
