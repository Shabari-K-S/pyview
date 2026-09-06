"""Animated progress bar element and live update handle."""

from __future__ import annotations

from typing import Any
from pyview.core.context import get_current_context


class ProgressElement:
    """Represents a progress bar element with live in-place update capability."""

    def __init__(self, element_id: str, props: dict[str, Any]) -> None:
        self.id = element_id
        self.props = props

    def progress(self, value: int | float, text: str | None = None) -> None:
        """Update the progress bar value and optional text."""
        pct = int(value * 100) if isinstance(value, float) and value <= 1.0 else int(value)
        self.props["value"] = max(0, min(100, pct))
        if text is not None:
            self.props["text"] = str(text)


def progress(
    value: int | float,
    text: str | None = None,
    key: str | None = None,
) -> ProgressElement:
    """Display a progress bar.

    `value` must be an int/float between 0 and 100 (or float 0.0 to 1.0).
    `text` is an optional description above or inside the progress bar.
    """
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("progress", key)

    pct = int(value * 100) if isinstance(value, float) and value <= 1.0 else int(value)
    normalized_value = max(0, min(100, pct))

    props = {
        "value": normalized_value,
        "text": str(text) if text is not None else None,
    }

    ctx.register_element({
        "type": "progress",
        "id": widget_id,
        "props": props,
    })

    return ProgressElement(widget_id, props)
