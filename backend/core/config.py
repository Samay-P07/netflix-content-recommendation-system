"""
Application Configuration
Loads settings from environment variables with safe development defaults.
"""

import os
from typing import List
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "CineMatch API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Dataset path resolution
    DATA_PATH: str = os.getenv(
        "DATA_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "Dataset.csv")
    )
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    # Database configuration (PostgreSQL)
    DB_USER: str = os.getenv("POSTGRES_USER", "postgres")
    DB_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    DB_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME: str = os.getenv("POSTGRES_DB", "cinematch")
    
    @property
    def DATABASE_URL(self) -> str:
        override_url = os.getenv("DATABASE_URL")
        if override_url:
            return override_url
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
