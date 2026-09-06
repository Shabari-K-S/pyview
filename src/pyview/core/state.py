"""Session state management for PyView.

Provides SessionState container for isolated per-session user data
and SessionStateProxy for clean module-level access via `pv.session_state`.
"""

from __future__ import annotations

from typing import Any, Iterator


class SessionState(dict):
    """A dictionary subclass that allows attribute-style access for session data."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"SessionState object has no attribute '{name}'") from None

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"SessionState object has no attribute '{name}'") from None

    def __repr__(self) -> str:
        return f"SessionState({super().__repr__()})"


class SessionStateProxy:
    """Dynamic proxy for accessing the current execution context's SessionState."""

    def _get_active_state(self) -> SessionState:
        # Import lazily to avoid circular dependencies
        from pyview.core.context import get_current_context

        ctx = get_current_context()
        return ctx.session.session_state

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_active_state(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._get_active_state(), name, value)

    def __delattr__(self, name: str) -> None:
        delattr(self._get_active_state(), name)

    def __getitem__(self, key: str) -> Any:
        return self._get_active_state()[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._get_active_state()[key] = value

    def __delitem__(self, key: str) -> None:
        del self._get_active_state()[key]

    def __contains__(self, key: object) -> bool:
        return key in self._get_active_state()

    def __iter__(self) -> Iterator[str]:
        return iter(self._get_active_state())

    def __len__(self) -> int:
        return len(self._get_active_state())

    def __repr__(self) -> str:
        try:
            return repr(self._get_active_state())
        except Exception:
            return "<SessionStateProxy (no active context)>"

    def get(self, key: str, default: Any = None) -> Any:
        return self._get_active_state().get(key, default)

    def setdefault(self, key: str, default: Any = None) -> Any:
        return self._get_active_state().setdefault(key, default)

    def pop(self, key: str, *args: Any) -> Any:
        return self._get_active_state().pop(key, *args)

    def keys(self):
        return self._get_active_state().keys()

    def values(self):
        return self._get_active_state().values()

    def items(self):
        return self._get_active_state().items()

    def clear(self) -> None:
        self._get_active_state().clear()

    def update(self, *args: Any, **kwargs: Any) -> None:
        self._get_active_state().update(*args, **kwargs)


# Global singleton proxy exposed as pv.session_state
session_state = SessionStateProxy()
