"""Two-way interactive and reactive data editor widget."""

from __future__ import annotations

from typing import Any, Dict, Optional
from pyview.components.data.data_utils import normalize_tabular_data, reconstruct_tabular_data
from pyview.core.context import get_current_context


def data_editor(
    data: Any,
    num_rows: str = "fixed",
    disabled: bool = False,
    key: Optional[str] = None,
    column_config: Optional[Dict[str, Any]] = None,
    hide_index: bool = False,
) -> Any:
    """Display an interactive and reactive data editor widget.

    Returns the edited dataset matching the input type (e.g. pandas DataFrame or list of dicts).
    """
    if num_rows not in ("fixed", "dynamic"):
        raise ValueError(f"data_editor num_rows must be 'fixed' or 'dynamic', got '{num_rows}'")

    ctx = get_current_context()
    widget_id = ctx.get_widget_id("data_editor", key)
    session = ctx.session

    if widget_id in ctx.pending_values:
        edited_raw = ctx.pending_values[widget_id]
        current_data = reconstruct_tabular_data(edited_raw, data)
        session.widget_values[widget_id] = current_data
        if key:
            session.session_state[key] = current_data
    elif widget_id in session.widget_values:
        current_data = session.widget_values[widget_id]
    elif key and key in session.session_state:
        current_data = session.session_state[key]
        session.widget_values[widget_id] = current_data
    else:
        current_data = data
        session.widget_values[widget_id] = current_data
        if key:
            session.session_state[key] = current_data

    normalized = normalize_tabular_data(current_data)

    serialized_config = {}
    if column_config and isinstance(column_config, dict):
        for col_name, cfg in column_config.items():
            if hasattr(cfg, "to_dict"):
                serialized_config[str(col_name)] = cfg.to_dict()
            elif isinstance(cfg, dict):
                serialized_config[str(col_name)] = cfg

    ctx.register_element({
        "type": "data_editor",
        "id": widget_id,
        "props": {
            "columns": normalized["columns"],
            "data": normalized["data"],
            "index": normalized["index"],
            "column_types": normalized.get("column_types", {}),
            "column_config": serialized_config,
            "num_rows": num_rows,
            "disabled": disabled,
            "hide_index": hide_index,
        },
    })

    return current_data
