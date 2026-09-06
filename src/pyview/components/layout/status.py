"""Stateful status container tracking asynchronous tasks."""

from __future__ import annotations

from pyview.components.base import Container
from pyview.core.context import get_current_context


class StatusContainer(Container):
    """Represents a stateful status disclosure container (e.g. running -> complete -> error)."""

    def update(
        self,
        label: str | None = None,
        state: str | None = None,
        expanded: bool | None = None,
    ) -> None:
        """Update the label, state, or expanded property of the status container."""
        if label is not None:
            self.props["label"] = str(label)
        if state is not None:
            if state not in ("running", "complete", "error"):
                raise ValueError(f"state must be one of 'running', 'complete', 'error', got '{state}'")
            self.props["state"] = state
        if expanded is not None:
            self.props["expanded"] = bool(expanded)


def status(
    label: str = "Running...",
    expanded: bool = False,
    state: str = "running",
    key: str | None = None,
) -> StatusContainer:
    """Create a collapsible status container that can display progress/logs of a task.

    Can be updated dynamically: `status.update(label="Complete!", state="complete", expanded=False)`.
    """
    if state not in ("running", "complete", "error"):
        raise ValueError(f"state must be one of 'running', 'complete', 'error', got '{state}'")

    ctx = get_current_context()
    status_id = ctx.get_widget_id("status", key)

    status_container = StatusContainer(
        id=status_id,
        type="status_container",
        props={
            "label": str(label),
            "state": state,
            "expanded": bool(expanded),
        },
    )
    ctx.register_element(status_container)
    return status_container
