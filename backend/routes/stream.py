"""
Stream Route
------------
Provides an MJPEG live stream from the inference worker.

Endpoint:  GET /api/stream
Content-Type: multipart/x-mixed-replace; boundary=frame

Open in any browser or <img> tag to see the live annotated camera feed.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.workers.inference_worker import shared_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stream", tags=["stream"])

_BOUNDARY = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
_BOUNDARY_END = b"\r\n"


async def _mjpeg_generator():
    """Async generator that yields MJPEG multipart frames."""
    while True:
        jpeg = shared_state.get_jpeg()
        if jpeg:
            yield _BOUNDARY + jpeg + _BOUNDARY_END
        # Yield control to the event loop — avoids blocking the server
        await asyncio.sleep(0.033)  # ~30 fps ceiling for the HTTP stream


@router.get(
    "",
    summary="Live MJPEG camera stream with YOLO + face annotations",
    response_description="Multipart MJPEG stream",
)
async def mjpeg_stream():
    """
    Stream the annotated camera feed as MJPEG.

    Compatible with:
    - Browser `<img src='/api/stream'>` tag
    - VLC / ffplay: `ffplay http://localhost:8000/api/stream`
    - curl: `curl http://localhost:8000/api/stream --output -`
    """
    return StreamingResponse(
        _mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Buffering": "no",  # important for nginx reverse proxy
        },
    )


@router.get(
    "/snapshot",
    summary="Get the latest annotated frame as a single JPEG image",
    response_description="JPEG image bytes",
)
async def snapshot():
    """Return the most recent annotated frame as a static JPEG image."""
    jpeg = shared_state.get_jpeg()
    if jpeg is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="No frame available yet.")
    return StreamingResponse(
        iter([jpeg]),
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store"},
    )
