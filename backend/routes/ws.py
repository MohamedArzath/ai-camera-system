"""
WebSocket Route
---------------
Pushes live detection results to connected clients every 500ms.

Endpoint:  WS /api/ws
Message format: JSON with detections, faces, reasoning, fps
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.workers.inference_worker import shared_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ws", tags=["websocket"])


@router.websocket("")
async def detection_websocket(websocket: WebSocket):
    """
    WebSocket endpoint — pushes latest detection results to the client every 500ms.
    Client receives JSON: { detections, faces, reasoning, fps, timestamp }
    """
    await websocket.accept()
    client = websocket.client
    logger.info("WebSocket client connected: %s", client)

    try:
        while True:
            data = shared_state.get_latest()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected: %s", client)
    except Exception as exc:
        logger.warning("WebSocket error for %s: %s", client, exc)
