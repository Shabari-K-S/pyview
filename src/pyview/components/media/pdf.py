"""Embedded PDF document viewer element."""

from __future__ import annotations

from typing import Any
from pyview.components.media.utils import process_pdf_to_data_url
from pyview.core.context import get_current_context


def pdf(
    data: Any,
    height: int | str = 500,
    width: int | str | None = None,
    key: str | None = None,
) -> None:
    """Display an embedded interactive PDF viewer.

    `data` can be:
    - PDF URL string (e.g. "https://...", "data:application/pdf;base64,...")
    - Local `.pdf` file path (`str` or `Path`)
    - Raw PDF `bytes` or `io.BytesIO`
    """
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("pdf", key)

    src = process_pdf_to_data_url(data)
    h_str = f"{height}px" if isinstance(height, (int, float)) else str(height)
    w_str = f"{width}px" if isinstance(width, (int, float)) else (str(width) if width else "100%")

    ctx.register_element({
        "type": "pdf",
        "id": widget_id,
        "props": {
            "src": src,
            "height": h_str,
            "width": w_str,
        },
    })
