"""
Inference Worker
----------------
TWO-THREAD DESIGN for maximum FPS:

Thread 1 – Fast loop  (InferenceWorker)
  Camera capture → YOLO → InsightFace → draw boxes → JPEG encode → SharedState
  Target: 15 FPS (configurable via WORKER_MAX_FPS).

Thread 2 – Slow loop  (QwenWorker)
  Picks the latest raw frame from a 1-slot queue → Qwen VLM inference → reasoning str
  Runs independently; never blocks the fast loop.

Thread-safety: all SharedState reads/writes are protected by a threading.Lock.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import List, Optional

import cv2
import numpy as np

from backend.ai.face_recognizer import FaceDetection, face_recognizer
from backend.ai.qwen_reasoning import qwen_reasoner
from backend.ai.yolo_detector import Detection, yolo_detector
from backend.config import (
    CAMERA_SOURCE,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    QWEN_REASON_INTERVAL,
    STREAM_JPEG_QUALITY,
    WORKER_MAX_FPS,
)

logger = logging.getLogger(__name__)


# ── Shared State ──────────────────────────────────────────────────────────────

@dataclass
class SharedState:
    """Thread-safe container for the latest inference results."""
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    raw_frame:    Optional[np.ndarray]  = None   # latest raw BGR frame (for Qwen)
    jpeg_frame:   Optional[bytes]       = None   # latest annotated JPEG bytes (for stream)
    detections:   List[Detection]       = field(default_factory=list)
    faces:        List[FaceDetection]   = field(default_factory=list)
    reasoning:    str                   = "Waiting for first frame…"
    running:      bool                  = False
    frame_timestamp: float              = 0.0
    fps:          float                 = 0.0

    def update_frame(
        self,
        raw_frame: np.ndarray,
        jpeg_frame: bytes,
        detections: List[Detection],
        faces: List[FaceDetection],
        fps: float,
    ) -> None:
        with self._lock:
            self.raw_frame       = raw_frame
            self.jpeg_frame      = jpeg_frame
            self.detections      = detections
            self.faces           = faces
            self.frame_timestamp = time.time()
            self.fps             = fps

    def update_reasoning(self, reasoning: str) -> None:
        with self._lock:
            self.reasoning = reasoning

    def get_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self.jpeg_frame

    def get_latest(self) -> dict:
        with self._lock:
            return {
                "detections": [
                    {
                        "label":      d.label,
                        "confidence": round(d.confidence, 3),
                        "bbox":       list(d.bbox),
                        "class_id":   d.class_id,
                        "track_id":   d.track_id,
                    }
                    for d in self.detections
                ],
                "faces": [
                    {
                        "confidence": round(f.confidence, 3),
                        "bbox":       list(f.bbox),
                    }
                    for f in self.faces
                ],
                "reasoning":       self.reasoning,
                "frame_timestamp": self.frame_timestamp,
                "fps":             round(self.fps, 1),
            }


# Global singleton
shared_state = SharedState()


# ── Thread 2: Qwen VLM Worker (slow, non-blocking) ───────────────────────────

class QwenWorker(threading.Thread):
    """
    Picks frames from a 1-slot queue and runs Qwen VLM reasoning.
    Updates shared_state.reasoning when done.
    Never blocks the fast camera loop.
    """

    def __init__(self, state: SharedState) -> None:
        super().__init__(name="QwenWorker", daemon=True)
        # maxsize=1: if Qwen is still running, discard newer frames silently
        self._queue: queue.Queue[tuple[np.ndarray, list[str]]] = queue.Queue(maxsize=1)
        self._state = state
        self._stop_event = threading.Event()

    def submit(self, frame: np.ndarray, labels: list[str]) -> None:
        """Non-blocking submit. Drops frame if queue is full (Qwen still busy)."""
        try:
            self._queue.put_nowait((frame, labels))
        except queue.Full:
            pass  # Qwen is busy — skip this frame, keeps camera loop unblocked

    def stop(self) -> None:
        self._stop_event.set()
        # Unblock the queue.get() call
        try:
            self._queue.put_nowait((None, []))  # type: ignore[arg-type]
        except queue.Full:
            pass

    def run(self) -> None:
        logger.info("QwenWorker: started.")
        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            frame, labels = item
            if frame is None:
                break  # sentinel — stop requested

            try:
                reasoning = qwen_reasoner.reason(frame, labels, force=True)
                self._state.update_reasoning(reasoning)
            except Exception as exc:
                logger.warning("QwenWorker: inference error: %s", exc)

        logger.info("QwenWorker: stopped.")


# ── Thread 1: Fast Camera + YOLO + InsightFace Loop ──────────────────────────

class InferenceWorker(threading.Thread):
    """
    Fast loop: capture → YOLO → InsightFace → annotate → JPEG → SharedState.
    Submits frames to QwenWorker every QWEN_REASON_INTERVAL seconds without
    waiting for the result — VLM reasoning never stalls this loop.
    """

    def __init__(self, state: SharedState, qwen_worker: QwenWorker) -> None:
        super().__init__(name="InferenceWorker", daemon=True)
        self._state        = state
        self._qwen         = qwen_worker
        self._stop_event   = threading.Event()
        self._min_loop_s   = 1.0 / WORKER_MAX_FPS

    def stop(self) -> None:
        logger.info("InferenceWorker: stop requested.")
        self._stop_event.set()

    def run(self) -> None:
        logger.info("InferenceWorker: opening camera source=%s", CAMERA_SOURCE)
        cap = cv2.VideoCapture(CAMERA_SOURCE)
        if not cap.isOpened():
            logger.error("InferenceWorker: cannot open camera source=%s", CAMERA_SOURCE)
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        # Reduce OpenCV internal buffer so we always get the *latest* frame
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self._state.running = True
        frame_count = 0
        fps_value   = 0.0
        fps_timer   = time.monotonic()
        last_qwen_submit = 0.0

        try:
            while not self._stop_event.is_set():
                loop_start = time.monotonic()

                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.warning("InferenceWorker: frame grab failed — retrying…")
                    time.sleep(0.05)
                    continue

                # ── YOLO ──────────────────────────────────────────────────────
                try:
                    detections = yolo_detector.detect(frame)
                except Exception as exc:
                    logger.warning("YOLO error: %s", exc)
                    detections = []

                # ── InsightFace ────────────────────────────────────────────────
                try:
                    faces = face_recognizer.detect_faces(frame)
                except Exception as exc:
                    logger.warning("InsightFace error: %s", exc)
                    faces = []

                # ── Submit to Qwen (non-blocking, throttled) ──────────────────
                now = time.monotonic()
                if now - last_qwen_submit >= QWEN_REASON_INTERVAL:
                    self._qwen.submit(frame.copy(), [d.label for d in detections])
                    last_qwen_submit = now

                # ── Annotate ───────────────────────────────────────────────────
                annotated = yolo_detector.draw_boxes(frame, detections)
                annotated = face_recognizer.draw_faces(annotated, faces)
                _draw_overlay(annotated, fps=fps_value, n_objects=len(detections))

                # ── JPEG encode ────────────────────────────────────────────────
                ok, buf = cv2.imencode(
                    ".jpg", annotated,
                    [cv2.IMWRITE_JPEG_QUALITY, STREAM_JPEG_QUALITY]
                )
                jpeg_bytes = buf.tobytes() if ok else b""

                # ── Update SharedState ─────────────────────────────────────────
                self._state.update_frame(
                    raw_frame=frame,
                    jpeg_frame=jpeg_bytes,
                    detections=detections,
                    faces=faces,
                    fps=fps_value,
                )

                # ── FPS tracking ───────────────────────────────────────────────
                frame_count += 1
                elapsed = time.monotonic() - fps_timer
                if elapsed >= 2.0:
                    fps_value   = frame_count / elapsed
                    frame_count = 0
                    fps_timer   = time.monotonic()

                # ── Rate limit ─────────────────────────────────────────────────
                sleep_s = self._min_loop_s - (time.monotonic() - loop_start)
                if sleep_s > 0:
                    time.sleep(sleep_s)

        finally:
            cap.release()
            self._state.running = False
            logger.info("InferenceWorker: stopped.")


# ── HUD overlay ───────────────────────────────────────────────────────────────

def _draw_overlay(frame: np.ndarray, fps: float, n_objects: int) -> None:
    h, w   = frame.shape[:2]
    margin = 10
    font   = cv2.FONT_HERSHEY_SIMPLEX
    scale  = 0.6
    thick  = 1

    for i, text in enumerate([f"FPS: {fps:.1f}", f"Objects: {n_objects}"]):
        (tw, th), _ = cv2.getTextSize(text, font, scale, thick)
        x = w - tw - margin
        y = margin + (th + 6) * (i + 1)
        cv2.putText(frame, text, (x + 1, y + 1), font, scale, (0, 0, 0), thick + 1, cv2.LINE_AA)
        cv2.putText(frame, text, (x, y),         font, scale, (0, 255, 0), thick,     cv2.LINE_AA)


# ── Module-level lifecycle ────────────────────────────────────────────────────

_worker: Optional[InferenceWorker] = None
_qwen_worker: Optional[QwenWorker] = None


def start_worker() -> None:
    global _worker, _qwen_worker
    if _worker is not None and _worker.is_alive():
        logger.warning("Workers already running — ignoring start.")
        return

    _qwen_worker = QwenWorker(shared_state)
    _qwen_worker.start()

    _worker = InferenceWorker(shared_state, _qwen_worker)
    _worker.start()

    logger.info("InferenceWorker + QwenWorker started.")


def stop_worker() -> None:
    global _worker, _qwen_worker
    if _qwen_worker:
        _qwen_worker.stop()
        _qwen_worker.join(timeout=5.0)
        _qwen_worker = None

    if _worker:
        _worker.stop()
        _worker.join(timeout=5.0)
        _worker = None
