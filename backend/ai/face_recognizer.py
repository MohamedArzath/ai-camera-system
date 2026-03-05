"""
InsightFace Face Detector
--------------------------
Detects and annotates faces in BGR frames using InsightFace (ArcFace backbone).
Draws face bounding boxes + a "Face" label on each detected face.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

import cv2
import numpy as np

from backend.config import INSIGHTFACE_DET_SIZE, INSIGHTFACE_MODEL

logger = logging.getLogger(__name__)

_FACE_COLOUR = (0, 255, 180)  # teal-green


@dataclass
class FaceDetection:
    bbox: tuple[int, int, int, int]          # x1, y1, x2, y2
    confidence: float
    embedding: list[float] = field(default_factory=list)  # 512-d ArcFace vector
    landmark: list | None = None


class FaceRecognizer:
    """Wraps InsightFace for face detection and embedding extraction."""

    def __init__(self) -> None:
        self._app = None

    def load(self) -> None:
        """Load the InsightFace model pack."""
        try:
            import insightface
            from insightface.app import FaceAnalysis

            logger.info(
                "Loading InsightFace model: %s  det_size=%s",
                INSIGHTFACE_MODEL,
                INSIGHTFACE_DET_SIZE,
            )
            self._app = FaceAnalysis(
                name=INSIGHTFACE_MODEL,
                providers=["CPUExecutionProvider"],
            )
            self._app.prepare(ctx_id=0, det_size=INSIGHTFACE_DET_SIZE)
            logger.info("InsightFace loaded successfully.")
        except Exception as exc:
            logger.error("Failed to load InsightFace: %s", exc)
            raise

    def detect_faces(self, frame: np.ndarray) -> List[FaceDetection]:
        """
        Detect faces in a BGR frame.

        Returns a list of FaceDetection objects.
        Returns an empty list (gracefully) if the model failed to load.
        """
        if self._app is None:
            return []

        try:
            # InsightFace expects BGR — matches OpenCV directly
            faces = self._app.get(frame)
        except Exception as exc:
            logger.warning("InsightFace inference error: %s", exc)
            return []

        results: List[FaceDetection] = []
        for face in faces:
            box = face.bbox.astype(int)
            x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
            conf = float(face.det_score)
            embedding = face.embedding.tolist() if face.embedding is not None else []
            landmark = (
                face.kps.tolist() if hasattr(face, "kps") and face.kps is not None else None
            )
            results.append(
                FaceDetection(
                    bbox=(x1, y1, x2, y2),
                    confidence=conf,
                    embedding=embedding,
                    landmark=landmark,
                )
            )

        return results

    def draw_faces(
        self,
        frame: np.ndarray,
        faces: List[FaceDetection],
    ) -> np.ndarray:
        """
        Draw face bounding boxes with confidence tag.
        Returns an annotated copy (does not modify original).
        """
        annotated = frame.copy()
        for face in faces:
            x1, y1, x2, y2 = face.bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), _FACE_COLOUR, 2)

            label = f"Face {face.confidence:.0%}"
            (tw, th), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            tag_y = max(y1 - 4, th + 4)
            cv2.rectangle(
                annotated,
                (x1, tag_y - th - baseline - 4),
                (x1 + tw + 4, tag_y),
                _FACE_COLOUR,
                cv2.FILLED,
            )
            cv2.putText(
                annotated,
                label,
                (x1 + 2, tag_y - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )

            # Draw facial landmarks (5 points)
            if face.landmark:
                for pt in face.landmark:
                    px, py = int(pt[0]), int(pt[1])
                    cv2.circle(annotated, (px, py), 2, (0, 200, 255), -1)

        return annotated


# ── Singleton ─────────────────────────────────────────────────────────────────
face_recognizer = FaceRecognizer()
