from __future__ import annotations
"""F-17 WebSocket endpoint — JWT authentication + heartbeat + real-timepush。"""
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.security import decode_token
from app.services.notifications.manager import ws_manager

log = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket connection endpoint.
    Clients connect via ws://host/ws?token=<JWT>.
    After verifying the JWT, the server maintains the connection and pushes real-time notifications.
    """
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        agency_id = payload.get("agency_id")  # M-06: extract agency_id used forisolation
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # M-06: use agency_id:user_id as the connection key to ensure broadcast isolation
    conn_key = f"{agency_id}:{user_id}" if agency_id else user_id
    await ws_manager.connect(websocket, conn_key)
    try:
        await websocket.send_json({"type": "connected"})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, conn_key)
    except Exception:
        ws_manager.disconnect(websocket, conn_key)
