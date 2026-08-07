import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Manually load the .env file from the correct location
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

load_dotenv(env_path)

class Settings(BaseSettings):
    # The name of our application - appears in API documentation and logs.
    app_name: str = "AI powered Invoice Intake and review system"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "doc_workflow"
    gemini_api_key: str | None = None
    # The Gemini model we use. gemini-2.5-flash is faster and better for beginners.
    llm_model: str = "gemini-2.5-flash"
    llm_timeout_seconds: int = 20
    # The default allowlist covers local development and the current production frontend.
    cors_origins: str = "http://localhost:5173,https://invoice-intake-and-review-system.vercel.app"
    storage_mode: str = "local"
    upload_dir: str = str(Path(__file__).resolve().parent.parent / "uploads")
    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None

    model_config = SettingsConfigDict(extra="ignore")

    # The app reads these values once at startup so bad env values fail fast with a clear error.
    @property
    def parsed_cors_origins(self) -> list[str]:
        origins = [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must contain at least one origin.")
        return origins

    # The upload mode must be explicit so production can use Cloudinary without relying on the Render disk.
    @property
    def use_cloudinary_storage(self) -> bool:
        mode = self.storage_mode.strip().lower()
        if mode not in {"local", "cloudinary"}:
            raise ValueError("STORAGE_MODE must be either 'local' or 'cloudinary'.")

        if mode == "cloudinary":
            missing_values = [
                name
                for name, value in (
                    ("CLOUDINARY_CLOUD_NAME", self.cloudinary_cloud_name),
                    ("CLOUDINARY_API_KEY", self.cloudinary_api_key),
                    ("CLOUDINARY_API_SECRET", self.cloudinary_api_secret),
                )
                if not value
            ]
            if missing_values:
                missing_list = ", ".join(missing_values)
                raise ValueError(f"Cloudinary storage requires these env vars: {missing_list}.")
            return True

        return False


settings = Settings()
