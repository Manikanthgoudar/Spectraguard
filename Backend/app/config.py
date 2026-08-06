from pydantic_settings import BaseSettings
from typing import List
import json
import os


class Settings(BaseSettings):
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "meheer17"
    DB_NAME: str = "spectraguard"

    # JWT
    JWT_SECRET_KEY: str = "spectraguard-super-secret-jwt-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File Storage
    UPLOAD_DIR: str = "uploads"
    REPORTS_DIR: str = "reports"
    SAMPLE_DATA_DIR: str = "sample_data"

    # CORS – accepts either "*" (wildcard) or a JSON array of origins
    CORS_ORIGINS: str = "*"

    # AI / Gemini
    GEMINI_API_KEY: str = ""

    # App
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def cors_origins_list(self) -> List[str]:
        val = self.CORS_ORIGINS.strip()
        if val == "*":
            return ["*"]
        try:
            parsed = json.loads(val)
            # If the list contains "*", collapse to just ["*"]
            if "*" in parsed:
                return ["*"]
            return parsed
        except Exception:
            return ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
