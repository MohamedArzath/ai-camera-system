"""
AI Camera System — FastAPI Application
---------------------------------------
Lifespan:  Loads all AI models at startup, starts the inference worker thread.
Routes:    /api/stream/*  and  /api/detect/*
Health:    GET /health
Docs:      GET /docs  (Swagger UI)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import CORS_ORIGINS
from backend.routes import detect as detect_router
from backend.routes import stream as stream_router
from backend.routes import ws as ws_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load AI models and start the inference worker at startup.
    Gracefully stop the worker at shutdown.
    """
    logger.info("=== AI Camera System starting up ===")

    # Import singletons
    from backend.ai.yolo_detector import yolo_detector
    from backend.ai.qwen_reasoning import qwen_reasoner
    from backend.ai.face_recognizer import face_recognizer
    from backend.workers.inference_worker import start_worker, stop_worker

    # Load each model (blocking — happens once before serving requests)
    logger.info("Loading YOLO …")
    try:
        yolo_detector.load()
    except Exception as exc:
        logger.error("YOLO load failed: %s  — continuing without YOLO.", exc)

    logger.info("Loading Qwen3.5-0.8B VLM …")
    try:
        qwen_reasoner.load()
    except Exception as exc:
        logger.error("Qwen load failed: %s  — continuing without VLM.", exc)

    logger.info("Loading InsightFace …")
    try:
        face_recognizer.load()
    except Exception as exc:
        logger.error("InsightFace load failed: %s  — continuing without face detection.", exc)

    # Start the camera capture + inference worker thread
    logger.info("Starting inference worker …")
    start_worker()

    logger.info("=== All systems ready. Serving requests. ===")

    yield  # ← FastAPI serves requests here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("=== AI Camera System shutting down ===")
    stop_worker()
    logger.info("Worker stopped. Goodbye.")


# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Camera System",
    description=(
        "Real-time object detection (YOLOv8), face recognition (InsightFace), "
        "and scene reasoning (Qwen3.5-0.8B VLM) over a live camera feed."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(stream_router.router)
app.include_router(detect_router.router)
app.include_router(ws_router.router)


# ── Top-level endpoints ────────────────────────────────────────────────────────

@app.get("/", tags=["root"])
async def root():
    return {
        "message": "AI Camera System API",
        "docs": "/docs",
        "stream": "/api/stream",
        "detect_latest": "/api/detect/latest",
        "health": "/health",
    }


@app.get("/health", tags=["root"])
async def health():
    from backend.workers.inference_worker import shared_state
    return {
        "status": "ok",
        "worker_running": shared_state.running,
        "fps": round(shared_state.fps, 1),
    }
