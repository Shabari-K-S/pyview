"""Static tabular dataset rendering."""

from __future__ import annotations

from typing import Any, Optional
from pyview.components.data.data_utils import normalize_tabular_data
from pyview.core.context import get_current_context


def table(data: Any, key: Optional[str] = None) -> None:
    """Display a static tabular dataset as a styled semantic HTML table."""
    normalized = normalize_tabular_data(data)
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("table", key)
    ctx.register_element({
        "type": "table",
        "id": widget_id,
        "props": {
            "columns": normalized["columns"],
            "data": normalized["data"],
            "index": normalized["index"],
            "column_types": normalized.get("column_types", {}),
        },
    })
