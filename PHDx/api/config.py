"""API Configuration."""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # API Settings
    api_title: str = "PHDx API"
    api_version: str = "1.0.0"
    debug: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Paths
    root_dir: Path = Path(__file__).parent.parent
    data_dir: Path = root_dir / "data"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
