"""Compatibility shim so `backend.app.main:app` works from the repo root."""

from __future__ import annotations

from pathlib import Path

_BACKEND_APP_DIR = Path(__file__).resolve().parent.parent / "backend" / "app"
__path__ = [str(_BACKEND_APP_DIR)]
