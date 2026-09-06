"""Execution context and ContextVar management for PyView.

Maintains per-thread/per-run isolation, hierarchical layout container stacks,
and container-scoped widget identity routing.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyview.components.base import Container
    from pyview.core.runtime import Session


@dataclass
class ExecutionContext:
    """Context holding the state and container hierarchy for a single script rerun."""

    session: Session
    generation: int = 0
    active_triggers: set[str] = field(default_factory=set)
    pending_values: dict[str, Any] = field(default_factory=dict)
    is_cancelled: bool = False
    page_config: Any = None
    query_params_mutated: bool = False

    # Hierarchical container stacks
    root_container: Container = field(default=None)  # type: ignore
    sidebar_container: Container = field(default=None)  # type: ignore
    container_stack: list[Container] = field(default_factory=list)

    def __post_init__(self) -> None:
        from pyview.components.base import Container

        if self.root_container is None:
            self.root_container = Container(id="root", type="root", props={}, children=[])
        if self.sidebar_container is None:
            self.sidebar_container = Container(id="sidebar", type="sidebar", props={}, children=[])
        if not self.container_stack:
            self.container_stack = [self.root_container]

    @property
    def current_container(self) -> Container:
        """Return the active container at the top of the context manager stack."""
        return self.container_stack[-1]

    @property
    def current_form_id(self) -> str | None:
        """Return the active form ID if inside a `with pv.form():` block, else None."""
        for c in reversed(self.container_stack):
            if c.type == "form":
                return c.props.get("form_id") or c.id
        return None

    def check_cancelled(self) -> None:
        """Immediately interrupt execution if this context has been superseded."""
        if self.is_cancelled:
            from pyview.core.flow import CancelledException
            raise CancelledException()

    def get_widget_id(self, widget_type: str, user_key: str | None) -> str:
        """Derive a stable, container-scoped widget ID from a user key or positional counter."""
        self.check_cancelled()
        if user_key is not None and user_key != "":
            return f"user_{user_key}"

        container = self.current_container
        count = container.positional_counters.get(widget_type, 0) + 1
        container.positional_counters[widget_type] = count

        # Build hierarchical path from active container stack
        path_segments = [c.id for c in self.container_stack if c.id not in ("root", "sidebar")]
        if self.current_container is self.sidebar_container:
            path_segments.insert(0, "sidebar")

        if path_segments:
            prefix = ".".join(path_segments)
            return f"{prefix}.{widget_type}_{count}"
        return f"{widget_type}_{count}"

    def register_element(self, element: Any) -> None:
        """Append an element node or container to the currently active container."""
        self.check_cancelled()
        self.current_container.children.append(element)

    def get_serialized_elements(self) -> list[dict[str, Any]]:
        """Serialize the complete root and sidebar container trees into JSON element arrays."""
        elements: list[dict[str, Any]] = []

        # Include sidebar elements if populated
        if self.sidebar_container.children:
            elements.append(self.sidebar_container.to_dict())

        # Include main content elements
        for child in self.root_container.children:
            if hasattr(child, "to_dict"):
                elements.append(child.to_dict())
            else:
                elements.append(child)

        return elements


_current_context: ContextVar[ExecutionContext | None] = ContextVar(
    "pyview_current_context", default=None
)


def get_current_context() -> ExecutionContext:
    """Retrieve the active ExecutionContext or raise a descriptive RuntimeError."""
    ctx = _current_context.get()
    if ctx is None:
        raise RuntimeError(
            "PyView widget or session_state accessed outside of an active script execution context. "
            "Make sure your script is running through the PyView runtime (e.g. `pyview run script.py`)."
        )
    return ctx


def set_current_context(ctx: ExecutionContext | None) -> Token:
    """Bind the current ExecutionContext to the context variable."""
    return _current_context.set(ctx)


def reset_current_context(token: Token) -> None:
    """Reset the context variable to its previous token state."""
    _current_context.reset(token)
