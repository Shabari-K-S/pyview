"""Color picker and file uploader widgets."""

from __future__ import annotations

from typing import Sequence
from pyview.core.context import get_current_context
from pyview.server.uploads import UploadedFile


def color_picker(
    label: str,
    value: str = "#388bfd",
    key: str | None = None,
) -> str:
    """Render a color picker with preview swatch."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("color_picker", key)
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
        "type": "color_picker",
        "id": widget_id,
        "props": {
            "label": str(label),
            "value": resolved_value,
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_value


def file_uploader(
    label: str,
    type: str | Sequence[str] | None = None,
    accept_multiple_files: bool = False,
    key: str | None = None,
) -> UploadedFile | list[UploadedFile] | None:
    """Render a file uploader dropzone widget with dedicated REST endpoint handling."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("file_uploader", key)
    session = ctx.session

    allowed_types: list[str] = []
    if type:
        if isinstance(type, str):
            allowed_types = [type]
        else:
            allowed_types = list(type)

    uploaded_obj = session.uploaded_files.get(widget_id)

    ctx.register_element({
        "type": "file_uploader",
        "id": widget_id,
        "props": {
            "label": str(label),
            "types": allowed_types,
            "multiple": bool(accept_multiple_files),
            "session_id": session.session_id,
            "has_file": bool(uploaded_obj),
            "file_name": uploaded_obj.name if uploaded_obj else None,
            "file_size": uploaded_obj.size if uploaded_obj else None,
            "form_id": ctx.current_form_id,
        },
    })

    return uploaded_obj
