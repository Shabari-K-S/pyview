"""Temporal input widgets: calendar date picker and Android-style radial clock time picker."""

from __future__ import annotations

import datetime
from typing import Any
from pyview.core.context import get_current_context


def date_input(
    label: str,
    value: Any = None,
    min_value: Any = None,
    max_value: Any = None,
    key: str | None = None,
) -> datetime.date:
    """Render a date input widget returning a native Python datetime.date object."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("date_input", key)
    session = ctx.session

    def to_date(val: Any) -> datetime.date:
        if isinstance(val, datetime.datetime):
            return val.date()
        if isinstance(val, datetime.date):
            return val
        if isinstance(val, str) and val.strip():
            return datetime.date.fromisoformat(val.strip())
        return datetime.date.today()

    default_date = to_date(value)

    if widget_id in ctx.pending_values:
        try:
            resolved_date = to_date(ctx.pending_values[widget_id])
        except Exception:
            resolved_date = default_date
        session.widget_values[widget_id] = resolved_date
        if key:
            session.session_state[key] = resolved_date
    elif key and key in session.session_state:
        resolved_date = to_date(session.session_state[key])
        session.widget_values[widget_id] = resolved_date
    elif widget_id in session.widget_values:
        resolved_date = to_date(session.widget_values[widget_id])
    else:
        resolved_date = default_date
        session.widget_values[widget_id] = default_date
        if key:
            session.session_state[key] = default_date

    min_iso = to_date(min_value).isoformat() if min_value else None
    max_iso = to_date(max_value).isoformat() if max_value else None

    ctx.register_element({
        "type": "date_input",
        "id": widget_id,
        "props": {
            "label": str(label),
            "value": resolved_date.isoformat(),
            "min_value": min_iso,
            "max_value": max_iso,
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_date


def time_input(
    label: str,
    value: Any = None,
    step: int = 60,
    key: str | None = None,
) -> datetime.time:
    """Render a time input widget returning a native Python datetime.time object."""
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("time_input", key)
    session = ctx.session

    def to_time(val: Any) -> datetime.time:
        if isinstance(val, datetime.datetime):
            return val.time()
        if isinstance(val, datetime.time):
            return val
        if isinstance(val, str) and val.strip():
            parts = val.strip().split(":")
            h = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 9
            m = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            s = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            return datetime.time(h, m, s)
        return datetime.time(9, 0, 0)

    default_time = to_time(value)

    if widget_id in ctx.pending_values:
        try:
            resolved_time = to_time(ctx.pending_values[widget_id])
        except Exception:
            resolved_time = default_time
        session.widget_values[widget_id] = resolved_time
        if key:
            session.session_state[key] = resolved_time
    elif key and key in session.session_state:
        resolved_time = to_time(session.session_state[key])
        session.widget_values[widget_id] = resolved_time
    elif widget_id in session.widget_values:
        resolved_time = to_time(session.widget_values[widget_id])
    else:
        resolved_time = default_time
        session.widget_values[widget_id] = default_time
        if key:
            session.session_state[key] = default_time

    ctx.register_element({
        "type": "time_input",
        "id": widget_id,
        "props": {
            "label": str(label),
            "value": resolved_time.strftime("%H:%M:%S"),
            "step": step,
            "form_id": ctx.current_form_id,
        },
    })

    return resolved_time
