"""Bidirectional reactive URL query parameter synchronization for PyView."""

from __future__ import annotations

from typing import Any, Iterator


class QueryParamsProxy:
    """Dynamic dictionary proxy for two-way URL query parameter synchronization."""

    def _get_active_dict(self) -> dict[str, Any]:
        from pyview.core.context import get_current_context
        ctx = get_current_context()
        return ctx.session.query_params

    def _mark_mutated(self) -> None:
        from pyview.core.context import get_current_context
        try:
            ctx = get_current_context()
            ctx.query_params_mutated = True
        except Exception:
            pass

    def __getitem__(self, key: str) -> Any:
        return self._get_active_dict()[str(key)]

    def __setitem__(self, key: str, value: Any) -> None:
        self._get_active_dict()[str(key)] = value
        self._mark_mutated()

    def __delitem__(self, key: str) -> None:
        del self._get_active_dict()[str(key)]
        self._mark_mutated()

    def __contains__(self, key: object) -> bool:
        return str(key) in self._get_active_dict()

    def __iter__(self) -> Iterator[str]:
        return iter(self._get_active_dict())

    def __len__(self) -> int:
        return len(self._get_active_dict())

    def get(self, key: str, default: Any = None) -> Any:
        return self._get_active_dict().get(str(key), default)

    def setdefault(self, key: str, default: Any = None) -> Any:
        if str(key) not in self._get_active_dict():
            self._get_active_dict()[str(key)] = default
            self._mark_mutated()
        return self._get_active_dict()[str(key)]

    def pop(self, key: str, *args: Any) -> Any:
        self._mark_mutated()
        return self._get_active_dict().pop(str(key), *args)

    def clear(self) -> None:
        self._get_active_dict().clear()
        self._mark_mutated()

    def update(self, *args: Any, **kwargs: Any) -> None:
        self._get_active_dict().update(*args, **kwargs)
        self._mark_mutated()

    def to_dict(self) -> dict[str, Any]:
        return dict(self._get_active_dict())

    def __repr__(self) -> str:
        try:
            return f"QueryParamsProxy({repr(self._get_active_dict())})"
        except Exception:
            return "<QueryParamsProxy (no active context)>"


# Global singleton proxy exposed as pv.query_params
query_params = QueryParamsProxy()
