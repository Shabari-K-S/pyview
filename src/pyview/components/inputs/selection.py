"""Selection widgets: selectbox, multiselect, radio, segmented control, and pills."""

from __future__ import annotations

from typing import Any, Sequence
from pyview.core.context import get_current_context


def selectbox(
    label: str,
    options: Sequence[Any],
    index: int = 0,
    key: str | None = None,
) -> Any:
    """Render a single-choice dropdown selectbox widget."""
    if not options or len(options) == 0:
        raise ValueError("selectbox options cannot be empty.")

    if index < 0 or index >= len(options):
        raise ValueError(
            f"selectbox index {index} is out of bounds for options sequence of length {len(options)}."
        )

    ctx = get_current_context()
    widget_id = ctx.get_widget_id("selectbox", key)
    session = ctx.session

    resolved_index: int = index

    if widget_id in ctx.pending_values:
        try:
            incoming_idx = int(ctx.pending_values[widget_id])
            if 0 <= incoming_idx < len(options):
                resolved_index = incoming_idx
        except (ValueError, TypeError):
            resolved_index = index
        session.widget_values[widget_id] = resolved_index
        if key:
            session.session_state[key] = options[resolved_index]
    elif key and key in session.session_state:
        stored_val = session.session_state[key]
        if stored_val in options:
            resolved_index = list(options).index(stored_val)
        elif isinstance(stored_val, int) and 0 <= stored_val < len(options):
            resolved_index = stored_val
        session.widget_values[widget_id] = resolved_index
    elif widget_id in session.widget_values:
        try:
            stored_idx = int(session.widget_values[widget_id])
            if 0 <= stored_idx < len(options):
                resolved_index = stored_idx
        except (ValueError, TypeError):
            resolved_index = index
    else:
        resolved_index = index
        session.widget_values[widget_id] = resolved_index
        if key:
            session.session_state[key] = options[resolved_index]

    resolved_value = options[resolved_index]
    option_labels = [str(opt) for opt in options]

    ctx.register_element({
        "type": "selectbox",
        "id": widget_id,
        "props": {
            "label": str(label),
            "options": option_labels,
            "selected_index": resolved_index,
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_value


def multiselect(
    label: str,
    options: Sequence[Any],
    default: Sequence[Any] | None = None,
    max_selections: int | None = None,
    placeholder: str = "Choose options...",
    key: str | None = None,
) -> list[Any]:
    """Render a multi-select dropdown tag widget."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("multiselect", key)
    session = ctx.session

    default_indices: list[int] = []
    if default:
        for item in default:
            if item in options:
                default_indices.append(list(options).index(item))
            elif isinstance(item, int) and 0 <= item < len(options):
                default_indices.append(item)

    resolved_indices: list[int] = default_indices

    if widget_id in ctx.pending_values:
        raw = ctx.pending_values[widget_id]
        if isinstance(raw, list):
            resolved_indices = []
            for item in raw:
                try:
                    idx = int(item)
                    if 0 <= idx < len(options) and idx not in resolved_indices:
                        resolved_indices.append(idx)
                except (ValueError, TypeError):
                    if item in options:
                        idx = list(options).index(item)
                        if idx not in resolved_indices:
                            resolved_indices.append(idx)
        session.widget_values[widget_id] = resolved_indices
        if key:
            session.session_state[key] = [options[i] for i in resolved_indices]
    elif key and key in session.session_state:
        stored = session.session_state[key]
        if isinstance(stored, list):
            resolved_indices = [list(options).index(x) for x in stored if x in options]
        session.widget_values[widget_id] = resolved_indices
    elif widget_id in session.widget_values:
        stored = session.widget_values[widget_id]
        if isinstance(stored, list):
            resolved_indices = [int(x) for x in stored if 0 <= int(x) < len(options)]
    else:
        resolved_indices = default_indices
        session.widget_values[widget_id] = resolved_indices
        if key:
            session.session_state[key] = [options[i] for i in resolved_indices]

    resolved_values = [options[i] for i in resolved_indices]
    option_labels = [str(opt) for opt in options]

    ctx.register_element({
        "type": "multiselect",
        "id": widget_id,
        "props": {
            "label": str(label),
            "options": option_labels,
            "selected_indices": resolved_indices,
            "max_selections": max_selections,
            "placeholder": str(placeholder),
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_values


def radio(
    label: str,
    options: Sequence[Any],
    index: int = 0,
    horizontal: bool = False,
    key: str | None = None,
) -> Any:
    """Render a single-choice radio button selector."""
    if not options or len(options) == 0:
        raise ValueError("radio options cannot be empty.")

    if index < 0 or index >= len(options):
        raise ValueError(f"radio index {index} is out of bounds for options sequence of length {len(options)}.")

    ctx = get_current_context()
    widget_id = ctx.get_widget_id("radio", key)
    session = ctx.session

    resolved_index: int = index

    if widget_id in ctx.pending_values:
        try:
            incoming_idx = int(ctx.pending_values[widget_id])
            if 0 <= incoming_idx < len(options):
                resolved_index = incoming_idx
        except (ValueError, TypeError):
            resolved_index = index
        session.widget_values[widget_id] = resolved_index
        if key:
            session.session_state[key] = options[resolved_index]
    elif key and key in session.session_state:
        stored_val = session.session_state[key]
        if stored_val in options:
            resolved_index = list(options).index(stored_val)
        elif isinstance(stored_val, int) and 0 <= stored_val < len(options):
            resolved_index = stored_val
        session.widget_values[widget_id] = resolved_index
    elif widget_id in session.widget_values:
        try:
            stored_idx = int(session.widget_values[widget_id])
            if 0 <= stored_idx < len(options):
                resolved_index = stored_idx
        except (ValueError, TypeError):
            resolved_index = index
    else:
        resolved_index = index
        session.widget_values[widget_id] = resolved_index
        if key:
            session.session_state[key] = options[resolved_index]

    resolved_value = options[resolved_index]
    option_labels = [str(opt) for opt in options]

    ctx.register_element({
        "type": "radio",
        "id": widget_id,
        "props": {
            "label": str(label),
            "options": option_labels,
            "selected_index": resolved_index,
            "horizontal": bool(horizontal),
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_value


def segmented_control(
    label: str,
    options: Sequence[Any],
    default: Any = None,
    selection_mode: str = "single",
    key: str | None = None,
) -> Any:
    """Render a segmented button bar / pills control."""
    if not options or len(options) == 0:
        raise ValueError("segmented_control options cannot be empty.")
    if selection_mode not in ("single", "multi"):
        raise ValueError(f"selection_mode must be 'single' or 'multi', got '{selection_mode}'")

    ctx = get_current_context()
    widget_id = ctx.get_widget_id("segmented_control", key)
    session = ctx.session

    if selection_mode == "single":
        if default is not None and default in options:
            default_val = default
        else:
            default_val = options[0]

        if widget_id in ctx.pending_values:
            raw = ctx.pending_values[widget_id]
            resolved_value = raw if raw in options else (options[int(raw)] if str(raw).isdigit() and int(raw) < len(options) else default_val)
            session.widget_values[widget_id] = resolved_value
            if key:
                session.session_state[key] = resolved_value
        elif key and key in session.session_state:
            resolved_value = session.session_state[key]
            session.widget_values[widget_id] = resolved_value
        elif widget_id in session.widget_values:
            resolved_value = session.widget_values[widget_id]
        else:
            resolved_value = default_val
            session.widget_values[widget_id] = default_val
            if key:
                session.session_state[key] = default_val
    else:
        default_list = list(default) if isinstance(default, (list, tuple, set)) else ([default] if default else [])
        if widget_id in ctx.pending_values:
            raw = ctx.pending_values[widget_id]
            resolved_value = [x for x in raw if x in options] if isinstance(raw, list) else []
            session.widget_values[widget_id] = resolved_value
            if key:
                session.session_state[key] = resolved_value
        elif key and key in session.session_state:
            resolved_value = session.session_state[key]
            session.widget_values[widget_id] = resolved_value
        elif widget_id in session.widget_values:
            resolved_value = session.widget_values[widget_id]
        else:
            resolved_value = default_list
            session.widget_values[widget_id] = default_list
            if key:
                session.session_state[key] = default_list

    ctx.register_element({
        "type": "segmented_control",
        "id": widget_id,
        "props": {
            "label": str(label),
            "options": [str(o) for o in options],
            "selected": resolved_value,
            "selection_mode": selection_mode,
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_value


def pills(
    label: str,
    options: Sequence[Any],
    default: Any = None,
    selection_mode: str = "single",
    key: str | None = None,
) -> Any:
    """Render a modern pills button selector (alias for segmented_control)."""
    return segmented_control(label, options=options, default=default, selection_mode=selection_mode, key=key)
