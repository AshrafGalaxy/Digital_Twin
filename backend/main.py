"""
main.py

Main entrypoint for the Digital Twin FastAPI modular monolith backend.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import check_db_health
from api.v1.router import api_v1_router
from api.v1.endpoints.stream import manager
from ingestion.mqtt_consumer import MQTTConsumer

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
    
    # 1. Check Database connection
    db_healthy = await check_db_health()
    if db_healthy:
        logger.info("PostgreSQL + PostGIS + TimescaleDB connection verified.")
    else:
        logger.warning("Database unavailable on startup. Operating in offline/degraded mode.")

    # 2. Start MQTT background consumer
    mqtt_consumer.start()
    
    yield

    # Shutdown sequence
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
