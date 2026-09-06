"""Interactive DataFrame grid with sorting, search, pagination, and CSV export."""

from __future__ import annotations

from typing import Any, Dict, Optional
from pyview.components.data.data_utils import normalize_tabular_data
from pyview.core.context import get_current_context


def dataframe(
    data: Any,
    use_container_width: bool = True,
    hide_index: bool = False,
    column_config: Optional[Dict[str, Any]] = None,
    height: Optional[int] = None,
    key: Optional[str] = None,
) -> None:
    """Display an interactive dataframe with search, sorting, pagination, and CSV download."""
    normalized = normalize_tabular_data(data)

    serialized_config = {}
    if column_config and isinstance(column_config, dict):
        for col_name, cfg in column_config.items():
            if hasattr(cfg, "to_dict"):
                serialized_config[str(col_name)] = cfg.to_dict()
            elif isinstance(cfg, dict):
                serialized_config[str(col_name)] = cfg

    ctx = get_current_context()
    widget_id = ctx.get_widget_id("dataframe", key)
    ctx.register_element({
        "type": "dataframe",
        "id": widget_id,
        "props": {
            "columns": normalized["columns"],
            "data": normalized["data"],
            "index": normalized["index"],
            "column_types": normalized.get("column_types", {}),
            "column_config": serialized_config,
            "use_container_width": use_container_width,
            "hide_index": hide_index,
            "height": height,
        },
    })
