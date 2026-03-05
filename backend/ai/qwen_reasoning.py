"""
Qwen3.5-0.8B Vision-Language Model Reasoning
---------------------------------------------
Uses the HuggingFace `transformers` pipeline for image-text-to-text inference.
This is the lightest approach — no external vLLM/SGLang server needed.

Model:  Qwen/Qwen3.5-0.8B
Task:   image-text-to-text
"""

from __future__ import annotations

import logging
import time
from typing import List

import cv2
import numpy as np
from PIL import Image

from backend.config import (
    QWEN_DEVICE,
    QWEN_MAX_NEW_TOKENS,
    QWEN_MODEL_ID,
    QWEN_REASON_INTERVAL,
)

logger = logging.getLogger(__name__)


def _frame_to_pil(frame: np.ndarray) -> Image.Image:
    """Convert a BGR OpenCV frame to a PIL RGB image."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def _build_prompt(detected_labels: List[str]) -> str:
    """Build the VLM user prompt, injecting YOLO-discovered labels for context."""
    if detected_labels:
        objects_str = ", ".join(set(detected_labels))
        hint = f"YOLO has already detected the following objects: {objects_str}. "
    else:
        hint = ""
    return (
        f"{hint}"
        "Analyse this camera frame. "
        "Briefly describe: (1) what objects/people are present, "
        "(2) what activity or situation is occurring, "
        "(3) any notable details or concerns. "
        "Be concise (2-3 sentences)."
    )


class QwenReasoner:
    """Wraps the Qwen3.5-0.8B VLM pipeline for throttled scene reasoning."""

    def __init__(self) -> None:
        self._pipe = None
        self._last_reason_time: float = 0.0
        self._last_result: str = "VLM not yet initialised."

    def load(self) -> None:
        """Load the Qwen VLM pipeline (downloads weights on first run)."""
        try:
            from transformers import pipeline  # local import

            logger.info(
                "Loading Qwen VLM pipeline: %s  (device=%s)", QWEN_MODEL_ID, QWEN_DEVICE
            )
            # torch_dtype="auto" lets HF pick bf16/fp16/fp32 based on device
            self._pipe = pipeline(
                "image-text-to-text",
                model=QWEN_MODEL_ID,
                device=QWEN_DEVICE,
                torch_dtype="auto",
            )
            logger.info("Qwen VLM pipeline loaded successfully.")
        except Exception as exc:
            logger.error("Failed to load Qwen VLM pipeline: %s", exc)
            raise

    @property
    def last_result(self) -> str:
        return self._last_result

    def reason(
        self,
        frame: np.ndarray,
        detected_labels: List[str] | None = None,
        force: bool = False,
    ) -> str:
        """
        Run VLM reasoning on the frame.

        Throttled by QWEN_REASON_INTERVAL seconds to avoid overloading.
        Returns the latest reasoning string (cached between calls).

        Args:
            frame:            BGR NumPy frame from OpenCV.
            detected_labels:  Labels from YOLO to inject as context.
            force:            Skip the throttle interval check.
        """
        if self._pipe is None:
            return "VLM not loaded."

        now = time.monotonic()
        if not force and (now - self._last_reason_time) < QWEN_REASON_INTERVAL:
            # Return cached result — not time to run again yet
            return self._last_result

        try:
            pil_image = _frame_to_pil(frame)
            prompt_text = _build_prompt(detected_labels or [])

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": pil_image},
                        {"type": "text", "text": prompt_text},
                    ],
                }
            ]

            output = self._pipe(
                text=messages,
                max_new_tokens=QWEN_MAX_NEW_TOKENS,
            )

            # Extract generated text from pipeline output
            if isinstance(output, list) and output:
                first = output[0]
                if isinstance(first, dict):
                    generated = first.get("generated_text", "")
                    # Pipeline may echo the full conversation — extract last assistant turn
                    if isinstance(generated, list):
                        for msg in reversed(generated):
                            if isinstance(msg, dict) and msg.get("role") == "assistant":
                                generated = msg.get("content", "")
                                break
                        else:
                            generated = str(generated)
                    self._last_result = str(generated).strip()
                else:
                    self._last_result = str(first).strip()

            self._last_reason_time = now
        except Exception as exc:
            logger.warning("Qwen inference error: %s", exc)
            self._last_result = f"VLM error: {exc}"

        return self._last_result


# ── Singleton ─────────────────────────────────────────────────────────────────
qwen_reasoner = QwenReasoner()
