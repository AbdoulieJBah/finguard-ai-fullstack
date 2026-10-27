"""Entry point kept for `uvicorn main:app` (local runs and the existing Railway start command)."""
from app.main import app

__all__ = ["app"]
