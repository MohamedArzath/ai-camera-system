"""
YOLO Object Detector
--------------------
Uses Ultralytics YOLOv8 to detect objects in BGR frames captured from OpenCV.
Draws annotated bounding boxes with label + confidence directly on frames.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

import cv2
import numpy as np

from backend.config import (
    YOLO_CONF_THRESHOLD,
    YOLO_DEVICE,
    YOLO_IOU_THRESHOLD,
    YOLO_MODEL,
)

logger = logging.getLogger(__name__)

# ── Colour palette – consistent per class id ──────────────────────────────────
_PALETTE = [
    (255, 56, 56),   # red
    (56, 255, 56),   # green
    (56, 56, 255),   # blue
    (255, 165, 0),   # orange
    (0, 255, 255),   # cyan
    (255, 0, 255),   # magenta
    (255, 215, 0),   # gold
    (148, 0, 211),   # violet
]


def _colour(class_id: int) -> tuple[int, int, int]:
    return _PALETTE[class_id % len(_PALETTE)]


@dataclass
class Detection:
    label: str
    confidence: float
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    class_id: int = 0
    track_id: int | None = None


class YOLODetector:
    """Wraps an Ultralytics YOLO model for easy frame-level inference."""

    def __init__(self) -> None:
        self._model = None

    def load(self) -> None:
        """Download (first run) and load the YOLO model."""
        try:
            from ultralytics import YOLO  # local import to keep startup fast

            logger.info("Loading YOLO model: %s on device=%s", YOLO_MODEL, YOLO_DEVICE)
            self._model = YOLO(YOLO_MODEL)
            # Warm-up with a blank frame
            dummy = np.zeros((320, 320, 3), dtype=np.uint8)
            self._model.predict(
                dummy,
                conf=YOLO_CONF_THRESHOLD,
                iou=YOLO_IOU_THRESHOLD,
                device=YOLO_DEVICE,
                verbose=False,
            )
            logger.info("YOLO model loaded successfully.")
        except Exception as exc:
            logger.error("Failed to load YOLO model: %s", exc)
            raise

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Run inference on a BGR frame.

        Returns a list of Detection objects sorted by confidence (descending).
        """
        if self._model is None:
            raise RuntimeError("YOLODetector not loaded. Call .load() first.")

        results = self._model.predict(
            frame,
            conf=YOLO_CONF_THRESHOLD,
            iou=YOLO_IOU_THRESHOLD,
            device=YOLO_DEVICE,
            verbose=False,
        )

        detections: List[Detection] = []
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                label = r.names.get(cls_id, str(cls_id))
                track_id = int(box.id[0]) if box.id is not None else None
                detections.append(
                    Detection(
                        label=label,
                        confidence=conf,
                        bbox=(x1, y1, x2, y2),
                        class_id=cls_id,
                        track_id=track_id,
                    )
                )

        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections

    def draw_boxes(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        show_conf: bool = True,
    ) -> np.ndarray:
        """
        Draw bounding boxes + label tags on a copy of the frame.
        Returns the annotated frame (does not modify original in-place).
        """
        annotated = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            colour = _colour(det.class_id)

            # Box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), colour, 2)

            # Label text
            label_text = det.label
            if show_conf:
                label_text += f" {det.confidence:.0%}"
            if det.track_id is not None:
                label_text += f" #{det.track_id}"

            # Background pill for readability
            (tw, th), baseline = cv2.getTextSize(
                label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1
            )
            tag_y = max(y1 - 4, th + 4)
            cv2.rectangle(
                annotated,
                (x1, tag_y - th - baseline - 4),
                (x1 + tw + 4, tag_y),
                colour,
                cv2.FILLED,
            )
            cv2.putText(
                annotated,
                label_text,
                (x1 + 2, tag_y - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )

        return annotated


# ── Singleton ─────────────────────────────────────────────────────────────────
yolo_detector = YOLODetector()
