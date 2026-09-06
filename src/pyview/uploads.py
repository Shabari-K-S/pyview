"""Compatibility shim for pyview.uploads (moved to pyview.server.uploads)."""

from pyview.server.uploads import UploadedFile

__all__ = [
    "UploadedFile",
]
