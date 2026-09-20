"""
stream.py

WebSocket connection manager and streaming endpoint for real-time state events.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["Streaming"])

class ReplayControlRequest(BaseModel):
    action: str = Field(..., description="Action: 'play', 'pause', 'seek', 'speed', 'jump_to_live'")
    minutes_ago: Optional[int] = Field(None, ge=0, le=720, description="Minutes in past (0 to 720)")
    speed: Optional[float] = Field(None, ge=1.0, le=10.0, description="Playback speed multiplier (1, 2, 5, 10)")

class ReplayStatusResponse(BaseModel):
    isPlaying: bool
    minutesAgo: int
    speed: float
    targetTime: str
    sourceMode: str

class StreamerControlRequest(BaseModel):
    action: str = Field(..., description="Action: 'start', 'stop', 'pause', 'resume', 'tick_once', 'set_interval'")
    interval_sec: Optional[float] = Field(None, ge=1.0, le=60.0, description="Tick interval in seconds")

class StreamerStatusResponse(BaseModel):
    isRunning: bool
    isPaused: bool
    ticksCount: int
    intervalSec: float
    lastTickAt: Optional[str]
    sourceMode: str

class ReplaySessionManager:
    """Manages active historical corridor replay playback session."""
    def __init__(self):
        self.is_playing: bool = False
        self.minutes_ago: int = 0
        self.speed: float = 1.0

    def get_status(self) -> Dict[str, Any]:
        now_utc = datetime.now(timezone.utc)
        target_dt = now_utc - timedelta(minutes=self.minutes_ago)
        source_mode = "REPLAY" if self.minutes_ago > 0 else "SIMULATION"
        return {
            "isPlaying": self.is_playing,
            "minutesAgo": self.minutes_ago,
            "speed": self.speed,
            "targetTime": target_dt.isoformat(),
            "sourceMode": source_mode
        }

    def execute_action(self, req: ReplayControlRequest) -> Dict[str, Any]:
        action = req.action.lower()
        if action == "play":
            self.is_playing = True
        elif action == "pause":
            self.is_playing = False
        elif action == "seek" and req.minutes_ago is not None:
            self.minutes_ago = req.minutes_ago
        elif action == "speed" and req.speed is not None:
            self.speed = req.speed
        elif action in ("jump_to_live", "live"):
            self.minutes_ago = 0
            self.is_playing = False

        return self.get_status()

replay_session = ReplaySessionManager()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("New WebSocket client connected. Total active: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket client disconnected. Total active: %d", len(self.active_connections))

    async def broadcast(self, message: Dict[str, Any]):
        message_json = json.dumps(message)
        stale_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception:
                stale_connections.append(connection)
                
        for stale in stale_connections:
            self.disconnect(stale)

manager = ConnectionManager()

@router.get("/replay/status", response_model=ReplayStatusResponse)
async def get_replay_status():
    """Returns the current historical corridor replay session status."""
    return replay_session.get_status()

@router.post("/replay/control", response_model=ReplayStatusResponse)
async def control_replay_stream(req: ReplayControlRequest):
    """
    Controls the digital twin historical corridor replay state.
    Broadcasts the state change to all active WebSocket clients.
    """
    status = replay_session.execute_action(req)
    # Broadcast event to connected dashboards
    await manager.broadcast({
        "eventType": "REPLAY_STATE_CHANGED",
        "payload": status
    })
    return status

@router.get("/simulator/status", response_model=StreamerStatusResponse)
async def get_simulator_status():
    """Returns the operational status of the embedded in-process corridor telemetry streamer."""
    from backend.ingestion.telemetry_streamer import telemetry_streamer
    return telemetry_streamer.get_status()

@router.post("/simulator/control", response_model=StreamerStatusResponse)
async def control_simulator_stream(req: StreamerControlRequest):
    """
    Controls the embedded in-process corridor telemetry streamer.
    Supports starting, stopping, pausing, resuming, triggering single tick, or setting tick interval.
    """
    from backend.ingestion.telemetry_streamer import telemetry_streamer
    action = req.action.lower()
    if action == "start":
        telemetry_streamer.start(broadcast_callback=manager.broadcast)
    elif action == "stop":
        telemetry_streamer.stop()
    elif action == "pause":
        telemetry_streamer.pause()
    elif action == "resume":
        telemetry_streamer.resume()
    elif action == "tick_once":
        await telemetry_streamer.tick_once()
    elif action == "set_interval" and req.interval_sec is not None:
        telemetry_streamer.set_interval(req.interval_sec)

    status = telemetry_streamer.get_status()
    await manager.broadcast({
        "eventType": "STREAMER_STATE_CHANGED",
        "payload": status
    })
    return status

@router.websocket("/state")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial welcome confirmation
        await websocket.send_text(json.dumps({
            "eventType": "CONNECTION_ESTABLISHED",
            "message": "Connected to Digital Twin real-time state stream"
        }))
        while True:
            # Keep connection alive; clients can send heartbeat pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"eventType": "PONG"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("WebSocket error: %s", exc)
        manager.disconnect(websocket)

