"""Numeric inputs, continuous sliders, and select sliders."""

from __future__ import annotations

from typing import Any, Sequence
from pyview.core.context import get_current_context


def slider(
    label: str,
    min_value: int | float = 0,
    max_value: int | float = 100,
    value: int | float | None = None,
    step: int | float | None = None,
    key: str | None = None,
) -> int | float:
    """Render a continuous range slider."""
    if min_value > max_value:
        raise ValueError(
            f"slider min_value ({min_value}) cannot be greater than max_value ({max_value})."
        )

    if value is None:
        value = min_value
    else:
        if not (min_value <= value <= max_value):
            raise ValueError(
                f"slider default value ({value}) must be within bounds [{min_value}, {max_value}]."
            )

    if step is None:
        step = 1.0 if isinstance(min_value, float) or isinstance(max_value, float) or isinstance(value, float) else 1

    ctx = get_current_context()
    widget_id = ctx.get_widget_id("slider", key)
    session = ctx.session

    if widget_id in ctx.pending_values:
        raw_val = ctx.pending_values[widget_id]
        resolved_value = float(raw_val) if isinstance(step, float) else int(float(raw_val))
        resolved_value = max(min_value, min(max_value, resolved_value))
        session.widget_values[widget_id] = resolved_value
        if key:
            session.session_state[key] = resolved_value
    elif key and key in session.session_state:
        stored = session.session_state[key]
        resolved_value = float(stored) if isinstance(step, float) else int(float(stored))
        resolved_value = max(min_value, min(max_value, resolved_value))
        session.widget_values[widget_id] = resolved_value
    elif widget_id in session.widget_values:
        resolved_value = session.widget_values[widget_id]
    else:
        resolved_value = value
        session.widget_values[widget_id] = value
        if key:
            session.session_state[key] = value

    ctx.register_element({
        "type": "slider",
        "id": widget_id,
        "props": {
            "label": str(label),
            "min_value": min_value,
            "max_value": max_value,
            "value": resolved_value,
            "step": step,
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_value


def select_slider(
    label: str,
    options: Sequence[Any],
    value: Any = None,
    key: str | None = None,
) -> Any:
    """Render a slider that snaps to discrete options."""
    if not options or len(options) == 0:
        raise ValueError("select_slider options cannot be empty.")

    ctx = get_current_context()
    widget_id = ctx.get_widget_id("select_slider", key)
    session = ctx.session

    init_idx = list(options).index(value) if value in options else 0

    if widget_id in ctx.pending_values:
        try:
            incoming_idx = int(ctx.pending_values[widget_id])
            resolved_index = max(0, min(len(options) - 1, incoming_idx))
        except (ValueError, TypeError):
            resolved_index = init_idx
        session.widget_values[widget_id] = resolved_index
        if key:
            session.session_state[key] = options[resolved_index]
    elif key and key in session.session_state:
        stored_val = session.session_state[key]
        resolved_index = list(options).index(stored_val) if stored_val in options else init_idx
        session.widget_values[widget_id] = resolved_index
    elif widget_id in session.widget_values:
        resolved_index = int(session.widget_values[widget_id])
    else:
        resolved_index = init_idx
        session.widget_values[widget_id] = init_idx
        if key:
            session.session_state[key] = options[init_idx]

    resolved_value = options[resolved_index]

    ctx.register_element({
        "type": "select_slider",
        "id": widget_id,
        "props": {
            "label": str(label),
            "options": [str(o) for o in options],
            "selected_index": resolved_index,
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_value


def number_input(
    label: str,
    min_value: int | float | None = None,
    max_value: int | float | None = None,
    value: int | float | None = None,
    step: int | float | None = None,
    key: str | None = None,
) -> int | float:
    """Render a numeric stepper input field."""
    if min_value is not None and max_value is not None and min_value > max_value:
        raise ValueError(
            f"number_input min_value ({min_value}) cannot be greater than max_value ({max_value})."
        )

    if value is None:
        value = min_value if min_value is not None else 0
    else:
        if min_value is not None and value < min_value:
            raise ValueError(f"value ({value}) cannot be less than min_value ({min_value}).")
        if max_value is not None and value > max_value:
            raise ValueError(f"value ({value}) cannot be greater than max_value ({max_value}).")

    if step is None:
        step = 1.0 if isinstance(value, float) or isinstance(min_value, float) or isinstance(max_value, float) else 1

    ctx = get_current_context()
    widget_id = ctx.get_widget_id("number_input", key)
    session = ctx.session

    if widget_id in ctx.pending_values:
        raw_val = ctx.pending_values[widget_id]
        resolved_value = float(raw_val) if isinstance(step, float) else int(float(raw_val))
        if min_value is not None:
            resolved_value = max(min_value, resolved_value)
        if max_value is not None:
            resolved_value = min(max_value, resolved_value)
        session.widget_values[widget_id] = resolved_value
        if key:
            session.session_state[key] = resolved_value
    elif key and key in session.session_state:
        stored = session.session_state[key]
        resolved_value = float(stored) if isinstance(step, float) else int(float(stored))
        if min_value is not None:
            resolved_value = max(min_value, resolved_value)
        if max_value is not None:
            resolved_value = min(max_value, resolved_value)
        session.widget_values[widget_id] = resolved_value
    elif widget_id in session.widget_values:
        resolved_value = session.widget_values[widget_id]
    else:
        resolved_value = value
        session.widget_values[widget_id] = value
        if key:
            session.session_state[key] = value

    ctx.register_element({
        "type": "number_input",
        "id": widget_id,
        "props": {
            "label": str(label),
            "min_value": min_value,
            "max_value": max_value,
            "value": resolved_value,
            "step": step,
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_value
