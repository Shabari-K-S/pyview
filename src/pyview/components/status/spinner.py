"""Rotating circular spinner with status message."""

from __future__ import annotations

from typing import Any
from pyview.core.context import get_current_context


class SpinnerContext:
    """Context manager for displaying a temporary spinner during code block execution."""

    def __init__(
        self,
        text: str = "In progress...",
        key: str | None = None,
        element: dict[str, Any] | None = None,
    ) -> None:
        self.text = text
        self.key = key
        self.element = element

    def __enter__(self) -> SpinnerContext:
        if self.element is None:
            ctx = get_current_context()
            widget_id = ctx.get_widget_id("spinner", self.key)
            self.element = {
                "type": "spinner",
                "id": widget_id,
                "props": {"text": str(self.text)},
            }
            ctx.register_element(self.element)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


def spinner(text: str = "In progress...", key: str | None = None) -> SpinnerContext:
    """Display a loading spinner with text message.

    Can be used as a context manager:
    ```python
    with pv.spinner("Training model..."):
        time.sleep(2)
    ```
    or called standalone to render a spinner element.
    """
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("spinner", key)
    element = {
        "type": "spinner",
        "id": widget_id,
        "props": {"text": str(text)},
    }
    ctx.register_element(element)
    return SpinnerContext(text=text, key=key, element=element)
