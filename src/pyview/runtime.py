"""Compatibility shim for pyview.runtime (moved to pyview.core.runtime)."""

from pyview.core.runtime import (
    ScriptRunner,
    Session,
    SessionManager,
    execute_session_run,
)

__all__ = [
    "Session",
    "SessionManager",
    "ScriptRunner",
    "execute_session_run",
]
