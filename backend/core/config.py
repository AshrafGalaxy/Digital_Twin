"""
config.py

Application configuration loaded from environment variables.
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True

    # Multi-Storage Persistence (P4-A)
    DATABASE_BACKEND: str = "auto"  # Options: "auto", "postgres", "sqlite"
    SQLITE_DB_PATH: str = "data/digital_twin.db"
    DB_CONNECT_TIMEOUT_SEC: float = 1.5

    # PostgreSQL / PostGIS / TimescaleDB
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "digital_twin"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432

    # MQTT Broker
    MQTT_BROKER_HOST: str = "127.0.0.1"
    MQTT_BROKER_PORT: int = 1883
    MQTT_CLIENT_ID: str = "digital_twin_backend"
    MQTT_USERNAME: str = "twin_service"
    MQTT_PASSWORD: str = "twin_secret_dev"

    # Embedded In-Process Telemetry Simulator Worker (P4-B)
    TELEMETRY_STREAMER_ENABLED: bool = True
    TELEMETRY_STREAMER_INTERVAL_SEC: float = 5.0
    TELEMETRY_STREAMER_MODE: str = "SIMULATION"  # Options: "SIMULATION", "REPLAY"

    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def resolved_sqlite_path(self) -> Path:
        path = Path(self.SQLITE_DB_PATH)
        if not path.is_absolute():
            # If current working directory has data/, use it; otherwise check parent data/
            if not (Path.cwd() / "data").exists() and (Path.cwd().parent / "data").exists():
                return (Path.cwd().parent / self.SQLITE_DB_PATH).resolve()
            return (Path.cwd() / path).resolve()
        return path

    @property
    def sqlite_async_url(self) -> str:
        resolved = self.resolved_sqlite_path
        resolved.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{resolved.as_posix()}"

    @property
    def sqlite_sync_url(self) -> str:
        resolved = self.resolved_sqlite_path
        resolved.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{resolved.as_posix()}"

    @property
    def sync_database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
