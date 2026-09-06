"""Celebratory full-screen particle physics effects (balloons & snow)."""

from __future__ import annotations

from pyview.core.context import get_current_context


def balloons(key: str | None = None) -> None:
    """Display celebratory floating balloons across the screen."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("balloons", key)
    ctx.register_element({
        "type": "balloons",
        "id": widget_id,
        "props": {},
    })


def snow(key: str | None = None) -> None:
    """Display celebratory falling snowflakes across the screen."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("snow", key)
    ctx.register_element({
        "type": "snow",
        "id": widget_id,
        "props": {},
    })
