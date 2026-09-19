"""
stream.py

WebSocket connection manager and streaming endpoint for real-time state events.
"""

import json
import logging
from typing import Any, Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["Streaming"])

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
