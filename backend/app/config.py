import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Manually load the .env file from the correct location
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

class Settings(BaseSettings):
    app_name: str = "AI Document Workflow Mini-System"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "doc_workflow"
    gemini_api_key: str | None = None
    llm_model: str = "gemini-2.0-flash"
    llm_timeout_seconds: int = 20
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(extra="ignore")


settings = Settings()
