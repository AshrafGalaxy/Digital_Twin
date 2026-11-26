"""
config.py

Application configuration loaded from environment variables.
"""

from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_FALLBACK_JWT_SECRET = "pune-dt-corridor-key-2026-viman-nagar"
INSECURE_DEFAULT_MQTT_PASSWORD = "twin_secret_dev"


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True

    # Multi-Storage Persistence (P4-A & ENH-02 Pool Recycling)
    DATABASE_BACKEND: str = "auto"  # Options: "auto", "postgres", "sqlite"
    DATABASE_URL: Optional[str] = None  # Full PostgreSQL connection string override
    SQLITE_DB_PATH: str = "data/digital_twin.db"
    DB_CONNECT_TIMEOUT_SEC: float = 1.5
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_HOSTED_POOL_SIZE: int = 5
    DB_HOSTED_MAX_OVERFLOW: int = 5
    DB_POOL_RECYCLE_SEC: int = 300

    # PostgreSQL / PostGIS / TimescaleDB
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "digital_twin"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432

    # Supabase Client Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

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

    # Temporal Alignment (Corridor Civil Time Offset from UTC; +330 = UTC+05:30 reference)
    CORRIDOR_UTC_OFFSET_MINUTES: int = 330
    # Study Area IANA Timezone (Default: Asia/Kolkata for reference corridor pilot)
    STUDY_AREA_TIMEZONE: str = "Asia/Kolkata"

    # Provenance Quality Score Baselines (AGENTS.md Section 3)
    SYNTHETIC_LOS_QUALITY_SCORE: float = 0.70  # Tier-0 zero-hardware synthetic baseline
    OBSERVED_LOS_QUALITY_SCORE: float = 0.98   # Physical sensor / verified live telemetry
    REPLAY_LOS_QUALITY_SCORE: float = 0.95     # Calibrated historical telemetry replay
    # |residual| / max(supply, demand). Above this share the balance is DEGRADED.
    POWER_BALANCE_RESIDUAL_SHARE_THRESHOLD: float = 0.05
    # Stopped or jammed density cannot exceed this many vehicles per km per lane.
    LOS_JAM_DENSITY_VEH_PER_KM_LANE: float = 180.0
    LOS_LANE_CAPACITY_VPH: float = 1800.0
    # Speeds below this are stopped. Density is not computed by substituting 1 km/h.
    LOS_STOPPED_SPEED_KMH: float = 1.0

    # API Server & Edge Controls (ENH-01)
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,testserver"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_REQUESTS: int = 25
    RATE_LIMIT_AUTH_WINDOW_SEC: int = 60
    RATE_LIMIT_COMPUTE_REQUESTS: int = 120
    RATE_LIMIT_COMPUTE_WINDOW_SEC: int = 60
    TRUST_PROXY_HEADERS: bool = False

    # Cryptographic Municipal Session Token Secret
    MUNICIPAL_JWT_SECRET: Optional[str] = None

    # Quarantine Storage Bounds & Retention Policy (BUG-32)
    QUARANTINE_RETENTION_HOURS: float = 168.0  # 7 days default retention
    QUARANTINE_MAX_RECORDS: int = 10000        # Maximum row cap to protect local spool against floods

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        return not self.is_production

    def validate_production_security(self) -> None:
        """
        Validates critical security settings for production mode.
        Fails fast if insecure fallback secrets or default passwords are used.
        """
        if self.is_production:
            if not self.MQTT_PASSWORD or self.MQTT_PASSWORD == INSECURE_DEFAULT_MQTT_PASSWORD:
                raise RuntimeError(
                    "Production environment refuses startup with insecure or default MQTT_PASSWORD."
                )
            if not self.MQTT_USERNAME:
                raise RuntimeError(
                    "Production environment requires a configured MQTT_USERNAME."
                )
            hosts = self.allowed_hosts_list
            if not hosts or "*" in hosts:
                raise RuntimeError(
                    "Production environment requires explicit ALLOWED_HOSTS without wildcards ('*')."
                )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_hosts_list(self) -> List[str]:
        return [host.strip().lower() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

    @property
    def is_exposed_beyond_localhost(self) -> bool:
        """Returns True when deployed in production or bound outside strict loopback interfaces."""
        bound_host = (self.API_HOST or "").strip().lower()
        return self.is_production or bound_host not in {"127.0.0.1", "localhost", "::1"}

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
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if "postgresql+asyncpg://" in url:
                url = url.replace("postgresql+asyncpg://", "postgresql://")
            return url
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
