"""Uploaded file abstractions and handlers for PyView."""

from __future__ import annotations

import io
from typing import Optional


class UploadedFile:
    """Represents a file uploaded by the user."""

    def __init__(
        self,
        name: str,
        size: int,
        type: str = "application/octet-stream",
        data: bytes = b"",
        content: bytes | None = None,
    ) -> None:
        self.name = name
        self.size = size
        self.type = type
        self.data = content if content is not None else data

    def getvalue(self) -> bytes:
        """Return the raw bytes of the uploaded file."""
        return self.data

    def read(self, size: Optional[int] = None) -> bytes:
        """Read bytes from the uploaded file."""
        if size is None or size < 0:
            return self.data
        return self.data[:size]

    def to_io(self) -> io.BytesIO:
        """Return a BytesIO stream for the uploaded file."""
        return io.BytesIO(self.data)

    def to_string(self, encoding: str = "utf-8") -> str:
        """Decode the uploaded file as a string."""
        return self.data.decode(encoding, errors="replace")

    def __repr__(self) -> str:
        return f"UploadedFile(name='{self.name}', type='{self.type}', size={self.size} bytes)"
