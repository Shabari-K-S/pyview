"""Boolean toggles and checkbox input widgets."""

from __future__ import annotations

from pyview.core.context import get_current_context


def checkbox(
    label: str,
    value: bool = False,
    key: str | None = None,
) -> bool:
    """Render a modern checkbox widget."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("checkbox", key)
    session = ctx.session

    if widget_id in ctx.pending_values:
        raw = ctx.pending_values[widget_id]
        resolved_value = bool(raw) if isinstance(raw, bool) else str(raw).lower() in ("true", "1", "yes")
        session.widget_values[widget_id] = resolved_value
        if key:
            session.session_state[key] = resolved_value
    elif key and key in session.session_state:
        resolved_value = bool(session.session_state[key])
        session.widget_values[widget_id] = resolved_value
    elif widget_id in session.widget_values:
        resolved_value = bool(session.widget_values[widget_id])
    else:
        resolved_value = bool(value)
        session.widget_values[widget_id] = resolved_value
        if key:
            session.session_state[key] = resolved_value

    ctx.register_element({
        "type": "checkbox",
        "id": widget_id,
        "props": {
            "label": str(label),
            "value": resolved_value,
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_value


def toggle(
    label: str,
    value: bool = False,
    key: str | None = None,
) -> bool:
    """Render a modern switch toggle."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("toggle", key)
    session = ctx.session

    if widget_id in ctx.pending_values:
        raw = ctx.pending_values[widget_id]
        resolved_value = bool(raw) if isinstance(raw, bool) else str(raw).lower() in ("true", "1", "yes")
        session.widget_values[widget_id] = resolved_value
        if key:
            session.session_state[key] = resolved_value
    elif key and key in session.session_state:
        resolved_value = bool(session.session_state[key])
        session.widget_values[widget_id] = resolved_value
    elif widget_id in session.widget_values:
        resolved_value = bool(session.widget_values[widget_id])
    else:
        resolved_value = bool(value)
        session.widget_values[widget_id] = resolved_value
        if key:
            session.session_state[key] = resolved_value

    ctx.register_element({
        "type": "toggle",
        "id": widget_id,
        "props": {
            "label": str(label),
            "value": resolved_value,
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_value
