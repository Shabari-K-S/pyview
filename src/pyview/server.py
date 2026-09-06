"""Compatibility shim for pyview.server (moved to pyview.server.app)."""

from pyview.server.app import STATIC_DIR, create_app

__all__ = [
    "create_app",
    "STATIC_DIR",
]
