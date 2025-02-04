from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    BASE_API_URL: str = "http://localhost:8000"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "BatterUp MLB API"

    # Firebase settings
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    FIREBASE_STORAGE_BUCKET: str = os.getenv("FIREBASE_STORAGE_BUCKET", "")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    GEMINI_KEY: str = os.getenv("GEMINI_KEY", "")

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React default port
        "http://localhost:8000",  # FastAPI docs
        "http://localhost:5173",  # NETHENOOB PORT
    ]

    DEVELOPMENT_MODE: bool = True

settings = Settings()