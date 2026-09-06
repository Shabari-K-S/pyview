"""Collapsible disclosure container with persisted toggle state."""

from __future__ import annotations

from pyview.components.base import Container
from pyview.core.context import get_current_context


class ExpanderContainer(Container):
    """Represents a collapsible disclosure container."""
    pass


def expander(
    label: str,
    expanded: bool = False,
    key: str | None = None,
) -> ExpanderContainer:
    """Create a collapsible accordion container.

    Open/closed toggle state is persisted across reruns via `session_state`.
    """
    ctx = get_current_context()
    expander_id = ctx.get_widget_id("expander", key)
    session = ctx.session

    # State Resolution for Expander Toggle:
    # 1. Incoming event value from active rerun (client clicked to toggle)
    # 2. User key in session_state
    # 3. Existing widget_values in session
    # 4. Default `expanded` parameter
    if expander_id in ctx.pending_values:
        raw_val = ctx.pending_values[expander_id]
        is_open = bool(raw_val) if isinstance(raw_val, bool) else str(raw_val).lower() in ("true", "1", "open")
        session.widget_values[expander_id] = is_open
        if key is not None and key != "":
            session.session_state[key] = is_open
    elif key is not None and key != "" and key in session.session_state:
        is_open = bool(session.session_state[key])
        session.widget_values[expander_id] = is_open
    elif expander_id in session.widget_values:
        is_open = bool(session.widget_values[expander_id])
    else:
        is_open = bool(expanded)
        session.widget_values[expander_id] = is_open
        if key is not None and key != "":
            session.session_state[key] = is_open

    expander_container = ExpanderContainer(
        id=expander_id,
        type="expander",
        props={"label": str(label), "expanded": is_open},
    )

    ctx.register_element(expander_container)
    return expander_container
