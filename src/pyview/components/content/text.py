"""Typography, markdown, and text display elements."""

from __future__ import annotations

import json as json_lib
from typing import Any
from pyview.core.context import get_current_context


def title(text: str, key: str | None = None) -> None:
    """Render a prominent page title heading."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("title", key)
    ctx.register_element({
        "type": "title",
        "id": widget_id,
        "props": {"text": str(text)},
    })


def header(text: str, key: str | None = None) -> None:
    """Render a section header."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("header", key)
    ctx.register_element({
        "type": "header",
        "id": widget_id,
        "props": {"text": str(text)},
    })


def write(*args: Any, key: str | None = None) -> None:
    """Render text, markdown, objects, or multiple arguments formatted automatically."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("write", key)

    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, (dict, list)):
            content = json_lib.dumps(arg, indent=2, default=str)
            content_type = "json"
        else:
            content = str(arg)
            content_type = "text"
    else:
        parts: list[str] = []
        for a in args:
            if isinstance(a, (dict, list)):
                parts.append(json_lib.dumps(a, default=str))
            else:
                parts.append(str(a))
        content = " ".join(parts)
        content_type = "text"

    ctx.register_element({
        "type": "write",
        "id": widget_id,
        "props": {
            "content": content,
            "content_type": content_type,
        },
    })
