"""
LiturgyBridge Real-time Synchronization Router.

This module exposes the WebSocket endpoint that connects visitor clients,
display beamers, and priest admin portals to synchronize the current gottesdienst section
in real-time.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(
    prefix="/sync",
    tags=["Real-time Synchronization"]
)

class ConnectionManager:
    """
    Manages active WebSocket connections for each running service.
    """
    def __init__(self):
        # Maps service_id -> list of active WebSockets
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, service_id: str, websocket: WebSocket):
        await websocket.accept()
        if service_id not in self.active_connections:
            self.active_connections[service_id] = []
        self.active_connections[service_id].append(websocket)

    def disconnect(self, service_id: str, websocket: WebSocket):
        if service_id in self.active_connections:
            self.active_connections[service_id].remove(websocket)
            if not self.active_connections[service_id]:
                del self.active_connections[service_id]

    async def broadcast(self, service_id: str, message: dict):
        """
        Sends a synchronization update (e.g. new active section ID)
        to all visitors and beamers connected to this service.
        """
        if service_id in self.active_connections:
            for connection in self.active_connections[service_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/services/{service_id}")
async def websocket_sync_endpoint(websocket: WebSocket, service_id: str):
    """
    Accepts WebSocket connections for real-time service tracking.
    """
    await manager.connect(service_id, websocket)
    try:
        while True:
            # Receive sync updates (e.g. from priest-assistant control portal)
            data = await websocket.receive_json()
            # Broadcast the update to all other connected clients
            await manager.broadcast(service_id, data)
    except WebSocketDisconnect:
        manager.disconnect(service_id, websocket)
