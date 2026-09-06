"""Styled exception callout with expandable monospace traceback."""

from __future__ import annotations

import traceback
from pyview.core.context import get_current_context


def exception(
    exception: Exception,
    key: str | None = None,
) -> None:
    """Display a formatted Python exception with expandable stack trace."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("exception", key)

    tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
    formatted_tb = "".join(tb_lines)

    ctx.register_element({
        "type": "exception",
        "id": widget_id,
        "props": {
            "error_type": type(exception).__name__,
            "message": str(exception),
            "traceback": formatted_tb,
        },
    })
