"""
main.py

Main entrypoint for the Digital Twin FastAPI modular monolith backend.
"""

from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend directory is in sys.path for direct or module execution
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.config import settings
from core.database import check_db_health, get_active_backend, get_persistence_info
from core.schema_migrator import init_db_schema
from api.v1.router import api_v1_router
from api.v1.endpoints.stream import manager
from ingestion.mqtt_consumer import MQTTConsumer
from ingestion.telemetry_streamer import telemetry_streamer

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("digital_twin")

# Initialize MQTT consumer with broadcast hook
mqtt_consumer = MQTTConsumer(broadcast_callback=manager.broadcast)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Digital Twin backend in %s mode...", settings.ENVIRONMENT)
    
    # 1. Multi-Storage Persistence: Initialize schema and seed corridor assets (P4-A)
    migration_res = await init_db_schema()
    backend_name = get_active_backend()
    if migration_res.get("status") == "INITIALIZED":
        logger.info(
            "Database persistence ready [%s]: %s tables verified, corridor assets primed.",
            "PostgreSQL (Primary)" if backend_name == "postgresql" else "SQLite (Resilient Local Engine)",
            migration_res.get("tablesCount", 18)
        )
    else:
        logger.warning("Database schema initialization notice: %s", migration_res)

    # 2. Start MQTT background consumer
    mqtt_consumer.start()

    # 3. Autonomous In-Process Corridor Telemetry Streamer (P4-B)
    if settings.TELEMETRY_STREAMER_ENABLED:
        logger.info("Starting autonomous corridor telemetry streamer worker...")
        telemetry_streamer.start(broadcast_callback=manager.broadcast)
    
    yield

    # Shutdown sequence
    if settings.TELEMETRY_STREAMER_ENABLED:
        logger.info("Stopping telemetry streamer worker...")
        await telemetry_streamer.stop_async()
    logger.info("Stopping MQTT background consumer...")
    mqtt_consumer.stop()
    logger.info("Digital Twin backend shutdown complete.")

app = FastAPI(
    title="Digital Twin — Smart City Analytics API",
    description="Backend API supporting the Viman Nagar–Somnath Nagar corridor digital twin.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API routes
app.include_router(api_v1_router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "Digital Twin Smart City Analytics API",
        "version": "1.0.0",
        "docsUrl": "/docs",
        "healthUrl": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)
