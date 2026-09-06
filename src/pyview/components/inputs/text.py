"""Text input, text area, and chat input widgets."""

from __future__ import annotations

from pyview.core.context import get_current_context


def text_input(
    label: str,
    value: str = "",
    key: str | None = None,
    placeholder: str = "",
    type: str = "text",
) -> str:
    """Render a single-line text input field."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("text_input", key)
    session = ctx.session

    if widget_id in ctx.pending_values:
        resolved_value = str(ctx.pending_values[widget_id])
        session.widget_values[widget_id] = resolved_value
        if key:
            session.session_state[key] = resolved_value
    elif key and key in session.session_state:
        resolved_value = str(session.session_state[key])
        session.widget_values[widget_id] = resolved_value
    elif widget_id in session.widget_values:
        resolved_value = str(session.widget_values[widget_id])
    else:
        resolved_value = str(value)
        session.widget_values[widget_id] = resolved_value
        if key:
            session.session_state[key] = resolved_value

    ctx.register_element({
        "type": "text_input",
        "id": widget_id,
        "props": {
            "label": str(label),
            "value": resolved_value,
            "placeholder": str(placeholder),
            "input_type": str(type),
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_value


def text_area(
    label: str,
    value: str = "",
    height: int = 120,
    placeholder: str = "",
    key: str | None = None,
) -> str:
    """Render a multi-line text area input field."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("text_area", key)
    session = ctx.session

    if widget_id in ctx.pending_values:
        resolved_value = str(ctx.pending_values[widget_id])
        session.widget_values[widget_id] = resolved_value
        if key:
            session.session_state[key] = resolved_value
    elif key and key in session.session_state:
        resolved_value = str(session.session_state[key])
        session.widget_values[widget_id] = resolved_value
    elif widget_id in session.widget_values:
        resolved_value = str(session.widget_values[widget_id])
    else:
        resolved_value = str(value)
        session.widget_values[widget_id] = resolved_value
        if key:
            session.session_state[key] = resolved_value

    ctx.register_element({
        "type": "text_area",
        "id": widget_id,
        "props": {
            "label": str(label),
            "value": resolved_value,
            "height": height,
            "placeholder": str(placeholder),
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_value


def chat_input(
    placeholder: str = "Ask a question...",
    key: str | None = None,
) -> str | None:
    """Render a conversational chat input prompt bar.

    Follows button transient semantics: returns the submitted string on the
    submission rerun, and resets to None on subsequent interactions.
    """
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("chat_input", key)

    submitted_text = None
    if widget_id in ctx.pending_values:
        val = ctx.pending_values[widget_id]
        if val and str(val).strip():
            submitted_text = str(val).strip()

    ctx.register_element({
        "type": "chat_input",
        "id": widget_id,
        "props": {
            "placeholder": str(placeholder),
        },
    })

    return submitted_text
