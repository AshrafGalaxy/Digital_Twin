"""
main.py

Main entrypoint for the Digital Twin FastAPI modular monolith backend.
"""

from contextlib import asynccontextmanager
import logging
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from backend.core.config import settings
    from backend.core.database import check_db_health, get_active_backend, get_persistence_info
    from backend.core.schema_migrator import init_db_schema
    from backend.api.v1.router import api_v1_router
    from backend.api.v1.endpoints.stream import manager
    from backend.ingestion.mqtt_consumer import MQTTConsumer
    from backend.ingestion.telemetry_streamer import telemetry_streamer
except ImportError:
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

@app.get("/health", tags=["Root"])
async def root_health():
    """System health and database connectivity ping per TECHNICAL_ARCHITECTURE.md §13.2."""
    is_healthy = await check_db_health()
    backend_name = get_active_backend()
    return {
        "status": "HEALTHY" if is_healthy else "DEGRADED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "status": "HEALTHY" if is_healthy else "ERROR",
            "activeBackend": backend_name,
            "details": get_persistence_info(),
            "error": None if is_healthy else "Database probe failed"
        }
    }

# Canonical WebSocket channels per TECHNICAL_ARCHITECTURE.md §13.3
@app.websocket("/ws/operations")
async def ws_operations(websocket: WebSocket):
    """Real-time operational twin feed (traffic, energy, environment state events)."""
    await manager.connect(websocket)
    try:
        await websocket.send_text(json.dumps({
            "eventType": "CONNECTION_ESTABLISHED",
            "channel": "operations",
            "message": "Connected to Digital Twin operational stream"
        }))
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"eventType": "PONG", "channel": "operations"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("WebSocket operations channel error: %s", exc)
        manager.disconnect(websocket)

@app.websocket("/ws/system")
async def ws_system(websocket: WebSocket):
    """Broker and pipeline health events, persistence status, and queue telemetry."""
    await websocket.accept()
    try:
        backend_name = get_active_backend()
        await websocket.send_text(json.dumps({
            "eventType": "SYSTEM_STATUS",
            "channel": "system",
            "database": backend_name,
            "streamerRunning": settings.TELEMETRY_STREAMER_ENABLED,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"eventType": "PONG", "channel": "system"}))
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("WebSocket system channel error: %s", exc)

@app.websocket("/ws/scenarios/{run_id}")
async def ws_scenarios(websocket: WebSocket, run_id: str):
    """Simulation progress and KPI telemetry stream for a specific scenario run."""
    await websocket.accept()
    try:
        try:
            from backend.services.scenario_service import ScenarioService
        except ImportError:
            from services.scenario_service import ScenarioService
        sc_svc = ScenarioService()
        run_data = sc_svc.get_run(run_id)
        await websocket.send_text(json.dumps({
            "eventType": "SCENARIO_PROGRESS",
            "runId": run_id,
            "status": run_data.get("status", "COMPLETED") if run_data else "NOT_FOUND",
            "kpis": run_data.get("kpiOutputs") if run_data else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"eventType": "PONG", "runId": run_id}))
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("WebSocket scenario stream error: %s", exc)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)
