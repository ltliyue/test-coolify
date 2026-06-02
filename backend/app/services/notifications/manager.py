from __future__ import annotations
"""WebSocket connection manager — in-memory, no Redis dependency."""
import logging
from typing import Dict, List, Any

from fastapi import WebSocket

log = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections, grouped by user_id."""

    def __init__(self) -> None:
        self._connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)
        log.info("WebSocket connected: user=%s (total=%d)", user_id, len(self._connections[user_id]))

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        if user_id in self._connections:
            self._connections[user_id] = [
                ws for ws in self._connections[user_id] if ws is not websocket
            ]
            if not self._connections[user_id]:
                del self._connections[user_id]
        log.info("WebSocket disconnected: user=%s", user_id)

    async def send_to_user(self, user_id: str, data: Dict[str, Any]) -> int:
        """Send a message to all connections of the specified user. Returns the number of successfully sent connections."""
        sent = 0
        connections = self._connections.get(user_id, [])
        dead: List[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_json(data)
                sent += 1
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, user_id)
        return sent

    async def broadcast_to_agency(self, agency_user_ids: List[str], data: Dict[str, Any]) -> int:
        """Broadcast a message to all online users within the agency."""
        total_sent = 0
        for uid in agency_user_ids:
            total_sent += await self.send_to_user(uid, data)
        return total_sent

    @property
    def active_connections_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


# Global singleton
ws_manager = ConnectionManager()
