"""Collapsible interactive JSON tree viewer."""

from __future__ import annotations

import json as json_lib
from typing import Any, Optional
from pyview.core.context import get_current_context


def json(body: Any, expanded: bool = True, key: Optional[str] = None) -> None:
    """Display an interactive collapsible JSON tree explorer with copy button."""
    if isinstance(body, str):
        try:
            parsed = json_lib.loads(body)
            json_str = json_lib.dumps(parsed, indent=2, default=str)
        except Exception:
            json_str = body
    else:
        try:
            json_str = json_lib.dumps(body, indent=2, default=str)
        except Exception:
            json_str = str(body)

    ctx = get_current_context()
    widget_id = ctx.get_widget_id("json_viewer", key)
    ctx.register_element({
        "type": "json_viewer",
        "id": widget_id,
        "props": {
            "raw_json": json_str,
            "expanded": bool(expanded),
        },
    })
