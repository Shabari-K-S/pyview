"""Compatibility shim for pyview.context (moved to pyview.core.context)."""

from pyview.core.context import (
    ExecutionContext,
    get_current_context,
    reset_current_context,
    set_current_context,
    _current_context,
)

__all__ = [
    "ExecutionContext",
    "get_current_context",
    "set_current_context",
    "reset_current_context",
    "_current_context",
]
