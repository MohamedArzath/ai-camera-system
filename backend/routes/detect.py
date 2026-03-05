"""
Detect Route
------------
REST API for detection results and on-demand single-frame inference.

Endpoints:
    GET  /api/detect/latest      → Latest detections from the live worker
    POST /api/detect/frame       → Run detection on an uploaded image
"""

from __future__ import annotations

import io
import logging
import time
from typing import Any, Dict, List

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.ai.face_recognizer import face_recognizer
from backend.ai.qwen_reasoning import qwen_reasoner
from backend.ai.yolo_detector import yolo_detector
from backend.workers.inference_worker import shared_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/detect", tags=["detect"])


# ── Response Models ────────────────────────────────────────────────────────────

class BoundingBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class DetectionResult(BaseModel):
    label: str
    confidence: float
    bbox: BoundingBox
    class_id: int
    track_id: int | None = None


class FaceResult(BaseModel):
    confidence: float
    bbox: BoundingBox


class InferenceResponse(BaseModel):
    detections: List[DetectionResult]
    faces: List[FaceResult]
    reasoning: str
    num_objects: int
    num_faces: int
    timestamp: float
    fps: float | None = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _det_to_model(d) -> DetectionResult:
    x1, y1, x2, y2 = d.bbox
    return DetectionResult(
        label=d.label,
        confidence=round(d.confidence, 4),
        bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
        class_id=d.class_id,
        track_id=d.track_id,
    )


def _face_to_model(f) -> FaceResult:
    x1, y1, x2, y2 = f.bbox
    return FaceResult(
        confidence=round(f.confidence, 4),
        bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get(
    "/latest",
    response_model=InferenceResponse,
    summary="Get the latest detection results from the live worker",
)
async def get_latest_detections():
    """
    Returns the most recent YOLO + InsightFace + Qwen results captured
    by the background inference worker.
    """
    raw = shared_state.get_latest()
    if not raw.get("frame_timestamp"):
        raise HTTPException(status_code=503, detail="Worker has not produced any frames yet.")

    detections = raw.get("detections", [])
    faces = raw.get("faces", [])

    return InferenceResponse(
        detections=[
            DetectionResult(
                label=d["label"],
                confidence=d["confidence"],
                bbox=BoundingBox(
                    x1=d["bbox"][0], y1=d["bbox"][1],
                    x2=d["bbox"][2], y2=d["bbox"][3],
                ),
                class_id=d["class_id"],
                track_id=d.get("track_id"),
            )
            for d in detections
        ],
        faces=[
            FaceResult(
                confidence=f["confidence"],
                bbox=BoundingBox(
                    x1=f["bbox"][0], y1=f["bbox"][1],
                    x2=f["bbox"][2], y2=f["bbox"][3],
                ),
            )
            for f in faces
        ],
        reasoning=raw.get("reasoning", ""),
        num_objects=len(detections),
        num_faces=len(faces),
        timestamp=raw.get("frame_timestamp", 0.0),
        fps=raw.get("fps"),
    )


@router.post(
    "/frame",
    response_model=InferenceResponse,
    summary="Run detection + VLM reasoning on a single uploaded image",
)
async def detect_uploaded_frame(file: UploadFile = File(...)):
    """
    Upload a JPEG/PNG image and run the full AI pipeline synchronously:
        YOLO → InsightFace → Qwen VLM reasoning.

    Returns detection results + VLM scene description.
    """
    # ── Read and decode image ──────────────────────────────────────────────────
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    np_arr = np.frombuffer(contents, dtype=np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(
            status_code=422,
            detail="Could not decode image. Ensure it is a valid JPEG or PNG.",
        )

    # ── Run inference ──────────────────────────────────────────────────────────
    try:
        detections = yolo_detector.detect(frame)
    except Exception as exc:
        logger.error("YOLO error on uploaded frame: %s", exc)
        detections = []

    try:
        faces = face_recognizer.detect_faces(frame)
    except Exception as exc:
        logger.error("InsightFace error on uploaded frame: %s", exc)
        faces = []

    try:
        detected_labels = [d.label for d in detections]
        reasoning = qwen_reasoner.reason(frame, detected_labels, force=True)
    except Exception as exc:
        logger.error("Qwen reasoning error on uploaded frame: %s", exc)
        reasoning = f"VLM error: {exc}"

    return InferenceResponse(
        detections=[_det_to_model(d) for d in detections],
        faces=[_face_to_model(f) for f in faces],
        reasoning=reasoning,
        num_objects=len(detections),
        num_faces=len(faces),
        timestamp=time.time(),
    )


@router.get(
    "/health",
    summary="Check the health of the inference pipeline",
)
async def pipeline_health():
    """Returns the status of each AI component including active compute device."""
    from backend.ai.yolo_detector import yolo_detector as yd
    from backend.ai.qwen_reasoning import qwen_reasoner as qr
    from backend.ai.face_recognizer import face_recognizer as fr
    from backend.config import YOLO_DEVICE, QWEN_DEVICE

    # Detect GPU availability
    cuda_available = False
    mps_available  = False
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        mps_available  = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    except Exception:
        pass

    # Resolve the effective device label for display
    def _device_label(cfg_device: str) -> str:
        d = cfg_device.lower()
        if d == "cuda":
            if cuda_available:
                try:
                    import torch
                    name = torch.cuda.get_device_name(0)
                    return f"cuda ({name})"
                except Exception:
                    return "cuda"
            return "cuda (unavailable — fallback to cpu)"
        if d == "mps":
            return "mps (Apple Silicon)" if mps_available else "mps (unavailable — fallback to cpu)"
        return "cpu"

    # InsightFace always runs on ONNX CPU provider (can be changed to CUDAExecutionProvider)
    insightface_provider = (
        "CUDAExecutionProvider" if cuda_available else "CPUExecutionProvider"
    )

    return {
        "yolo":               "loaded" if yd._model is not None else "not_loaded",
        "yolo_device":        _device_label(YOLO_DEVICE),
        "qwen":               "loaded" if qr._pipe is not None else "not_loaded",
        "qwen_device":        _device_label(QWEN_DEVICE),
        "insightface":        "loaded" if fr._app is not None else "not_loaded",
        "insightface_device": insightface_provider,
        "cuda_available":     cuda_available,
        "mps_available":      mps_available,
        "worker_running":     shared_state.running,
        "fps":                round(shared_state.fps, 1),
    }
