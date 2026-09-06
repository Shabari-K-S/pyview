"""Interactive sentiment and star rating feedback widgets."""

from __future__ import annotations

from pyview.core.context import get_current_context


def feedback(
    options: str = "stars",
    key: str | None = None,
) -> int | None:
    """Render an interactive sentiment or star rating feedback widget.

    `options` supports: "stars" (1-5), "thumbs" (0-1), "faces" (1-5).
    Returns rating integer or None if not yet rated.
    """
    if options not in ("stars", "thumbs", "faces"):
        raise ValueError(f"feedback options must be 'stars', 'thumbs', or 'faces', got '{options}'")

    ctx = get_current_context()
    widget_id = ctx.get_widget_id("feedback", key)
    session = ctx.session

    if widget_id in ctx.pending_values:
        raw = ctx.pending_values[widget_id]
        resolved_value = int(raw) if raw is not None and str(raw).isdigit() else None
        session.widget_values[widget_id] = resolved_value
        if key:
            session.session_state[key] = resolved_value
    elif key and key in session.session_state:
        resolved_value = session.session_state[key]
        session.widget_values[widget_id] = resolved_value
    elif widget_id in session.widget_values:
        resolved_value = session.widget_values[widget_id]
    else:
        resolved_value = None
        session.widget_values[widget_id] = None
        if key:
            session.session_state[key] = None

    ctx.register_element({
        "type": "feedback",
        "id": widget_id,
        "props": {
            "feedback_type": options,
            "value": resolved_value,
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_value
