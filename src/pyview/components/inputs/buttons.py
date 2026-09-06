"""Button and trigger action controls."""

from __future__ import annotations

import base64
from typing import Any
from pyview.core.context import get_current_context


def button(label: str, key: str | None = None) -> bool:
    """Render a clickable push button widget.

    Returns True ONLY during the rerun triggered by clicking the button.
    Automatically resets to False on subsequent reruns.
    """
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("button", key)
    is_clicked = widget_id in ctx.active_triggers

    ctx.register_element({
        "type": "button",
        "id": widget_id,
        "props": {
            "label": str(label),
        },
    })

    return is_clicked


def download_button(
    label: str,
    data: Any,
    file_name: str = "download.txt",
    mime: str | None = None,
    key: str | None = None,
) -> bool:
    """Render a client-side direct download button with Base64 embedded data URI."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("download_button", key)
    is_clicked = widget_id in ctx.active_triggers

    if isinstance(data, bytes):
        raw_bytes = data
        mime_type = mime or "application/octet-stream"
    elif isinstance(data, str):
        raw_bytes = data.encode("utf-8")
        mime_type = mime or "text/plain;charset=utf-8"
    elif hasattr(data, "to_csv"):
        raw_bytes = data.to_csv(index=False).encode("utf-8")
        mime_type = mime or "text/csv"
    else:
        raw_bytes = str(data).encode("utf-8")
        mime_type = mime or "text/plain;charset=utf-8"

    b64_str = base64.b64encode(raw_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64_str}"

    ctx.register_element({
        "type": "download_button",
        "id": widget_id,
        "props": {
            "label": str(label),
            "file_name": str(file_name),
            "data_url": data_url,
        },
    })

    return is_clicked


def link_button(
    label: str,
    url: str,
    key: str | None = None,
) -> None:
    """Render an outbound hyperlinked button."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("link_button", key)
    ctx.register_element({
        "type": "link_button",
        "id": widget_id,
        "props": {
            "label": str(label),
            "url": str(url),
        },
    })


def form_submit_button(label: str = "Submit", key: str | None = None) -> bool:
    """Render a form submit button.

    Returns True ONLY during the rerun triggered by submitting the form.
    Must be called inside a `with pv.form():` container.
    """
    ctx = get_current_context()
    form_id = ctx.current_form_id
    if not form_id:
        raise RuntimeError("pv.form_submit_button must be called inside a `with pv.form():` block.")

    widget_id = ctx.get_widget_id("form_submit_button", key)
    is_clicked = widget_id in ctx.active_triggers

    ctx.register_element({
        "type": "form_submit_button",
        "id": widget_id,
        "props": {
            "label": str(label),
            "form_id": form_id,
        },
    })

    return is_clicked
