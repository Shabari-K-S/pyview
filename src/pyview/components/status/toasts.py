"""Floating corner toast notifications."""

from __future__ import annotations

from pyview.core.context import get_current_context


def toast(
    body: str,
    icon: str | None = None,
    key: str | None = None,
) -> None:
    """Display a brief floating toast notification in the corner of the screen."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("toast", key)
    ctx.register_element({
        "type": "toast",
        "id": widget_id,
        "props": {
            "body": str(body),
            "icon": str(icon) if icon is not None else "💬",
        },
    })
