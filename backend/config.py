"""
Centralized configuration for the AI Camera System.
All tuneable parameters live here.
"""

import os


def _auto_device() -> str:
    """Pick the best available compute device: cuda > mps > cpu."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"

_DEFAULT_DEVICE: str = _auto_device()

# ─── Camera ───────────────────────────────────────────────────────────────────
# 0 = default webcam; set to a stream URL (rtsp://...) for IP cameras
CAMERA_SOURCE: int | str = int(os.getenv("CAMERA_SOURCE", "0"))

# Target capture resolution
FRAME_WIDTH: int = int(os.getenv("FRAME_WIDTH", "1280"))
FRAME_HEIGHT: int = int(os.getenv("FRAME_HEIGHT", "720"))

# ─── YOLO ─────────────────────────────────────────────────────────────────────
# yolov8n = nano (fastest), yolov8s = small, yolov8m = medium
YOLO_MODEL: str = os.getenv("YOLO_MODEL", "yolov8n.pt")
YOLO_CONF_THRESHOLD: float = float(os.getenv("YOLO_CONF", "0.45"))
YOLO_IOU_THRESHOLD: float = float(os.getenv("YOLO_IOU", "0.45"))
YOLO_DEVICE: str = os.getenv("YOLO_DEVICE", _DEFAULT_DEVICE)  # "cpu" | "cuda" | "mps"

# ─── Qwen VLM ─────────────────────────────────────────────────────────────────
QWEN_MODEL_ID: str = os.getenv("QWEN_MODEL_ID", "Qwen/Qwen3.5-0.8B")
# Max new tokens the VLM can generate per frame
QWEN_MAX_NEW_TOKENS: int = int(os.getenv("QWEN_MAX_NEW_TOKENS", "150"))
# How often (in seconds) to run VLM reasoning (expensive — throttled separately)
QWEN_REASON_INTERVAL: float = float(os.getenv("QWEN_REASON_INTERVAL", "3.0"))
QWEN_DEVICE: str = os.getenv("QWEN_DEVICE", _DEFAULT_DEVICE)  # "cpu" | "cuda" | "mps"

# ─── InsightFace ───────────────────────────────────────────────────────────────
INSIGHTFACE_MODEL: str = os.getenv("INSIGHTFACE_MODEL", "buffalo_l")
# Detection size; lower = faster
INSIGHTFACE_DET_SIZE: tuple[int, int] = (
    int(os.getenv("INSIGHTFACE_DET_W", "320")),
    int(os.getenv("INSIGHTFACE_DET_H", "320")),
)

# ─── Worker ───────────────────────────────────────────────────────────────────
# Max frames-per-second the inference worker loop will process
WORKER_MAX_FPS: float = float(os.getenv("WORKER_MAX_FPS", "15.0"))

# ─── MJPEG Stream ─────────────────────────────────────────────────────────────
# JPEG quality for the live stream (1-95)
STREAM_JPEG_QUALITY: int = int(os.getenv("STREAM_JPEG_QUALITY", "80"))

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Comma-separated list of allowed origins for the frontend
CORS_ORIGINS: list[str] = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
).split(",")
