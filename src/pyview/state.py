"""Compatibility shim for pyview.state (moved to pyview.core.state)."""

from pyview.core.state import SessionState, SessionStateProxy, session_state

__all__ = [
    "SessionState",
    "SessionStateProxy",
    "session_state",
]
