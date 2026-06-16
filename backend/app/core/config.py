import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "NayePankh InsightHub API"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DATA_ROOT: str = "./data"
    DATABASE_URL: str | None = None
    FRONTEND_ORIGINS: str | None = None
    ALLOWED_ORIGINS: str | None = None
    DEBUG: bool = True

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_TIMEOUT_SECONDS: int = 45

    @property
    def data_root_dir(self) -> Path:
        # If it's absolute, return it directly
        path = Path(self.DATA_ROOT)
        if path.is_absolute():
            return path
        # For relative paths, resolve relative to the backend project root (which contains app/ and data/)
        backend_root = Path(__file__).resolve().parent.parent.parent
        return (backend_root / self.DATA_ROOT).resolve()

    @property
    def db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        db_path = self.data_root_dir / "nayepankh_insighthub.db"
        return f"sqlite:///{db_path.as_posix()}"


    @property
    def cors_origins_list(self) -> list[str]:
        origins_str = self.ALLOWED_ORIGINS or self.FRONTEND_ORIGINS or "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001"
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

