"""Alert cards (success, info, warning, error), horizontal dividers, and KPI metrics."""

from __future__ import annotations

from typing import Any
from pyview.core.context import get_current_context


def success(text: str, icon: str = "✅", key: str | None = None) -> None:
    """Render a green success alert card."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("success", key)
    ctx.register_element({
        "type": "alert",
        "id": widget_id,
        "props": {
            "text": str(text),
            "icon": str(icon),
            "alert_type": "success",
        },
    })


def info(text: str, icon: str = "ℹ️", key: str | None = None) -> None:
    """Render a blue informational alert card."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("info", key)
    ctx.register_element({
        "type": "alert",
        "id": widget_id,
        "props": {
            "text": str(text),
            "icon": str(icon),
            "alert_type": "info",
        },
    })


def warning(text: str, icon: str = "⚠️", key: str | None = None) -> None:
    """Render an amber caution warning card."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("warning", key)
    ctx.register_element({
        "type": "alert",
        "id": widget_id,
        "props": {
            "text": str(text),
            "icon": str(icon),
            "alert_type": "warning",
        },
    })


def error(text: str, icon: str = "❌", key: str | None = None) -> None:
    """Render a red danger error card."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("error", key)
    ctx.register_element({
        "type": "alert",
        "id": widget_id,
        "props": {
            "text": str(text),
            "icon": str(icon),
            "alert_type": "error",
        },
    })


def divider(key: str | None = None) -> None:
    """Render a horizontal divider rule."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("divider", key)
    ctx.register_element({
        "type": "divider",
        "id": widget_id,
        "props": {},
    })


def metric(
    label: str,
    value: Any,
    delta: Any = None,
    delta_color: str = "normal",
    key: str | None = None,
) -> None:
    """Render a KPI metric card with label, value, and optional delta indicator.

    delta_color accepts:
    - 'normal': positive is green, negative is red (default)
    - 'inverse': positive is red, negative is green (e.g. cost/churn)
    - 'off': delta is rendered in neutral gray
    """
    if delta_color not in ("normal", "inverse", "off"):
        raise ValueError(
            f"metric delta_color must be one of ('normal', 'inverse', 'off'), got '{delta_color}'"
        )

    delta_str = str(delta) if delta is not None else None
    delta_direction = "neutral"

    if delta_str is not None:
        stripped = delta_str.strip()
        if stripped.startswith("+"):
            delta_direction = "positive"
        elif stripped.startswith("-"):
            delta_direction = "negative"
        else:
            try:
                numeric_val = float(stripped.replace("%", "").replace(",", "").replace("$", ""))
                if numeric_val > 0:
                    delta_direction = "positive"
                elif numeric_val < 0:
                    delta_direction = "negative"
                else:
                    delta_direction = "neutral"
            except (ValueError, TypeError):
                delta_direction = "neutral"

    ctx = get_current_context()
    widget_id = ctx.get_widget_id("metric", key)
    ctx.register_element({
        "type": "metric",
        "id": widget_id,
        "props": {
            "label": str(label),
            "value": str(value),
            "delta": delta_str,
            "delta_color": delta_color,
            "delta_direction": delta_direction,
        },
    })
