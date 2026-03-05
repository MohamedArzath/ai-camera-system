"""
Root entrypoint — re-exports the FastAPI app from backend/main.py.

Run with:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Or for production (VPS deployment):
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
    (single worker is required — models are loaded into a single process memory)
"""

from backend.main import app  # noqa: F401  (re-export for uvicorn)

__all__ = ["app"]