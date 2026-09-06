"""Dedicated sidebar panel proxy singleton."""

from __future__ import annotations

from typing import Any
from pyview.components.base import Container
from pyview.core.context import get_current_context


class SidebarProxy:
    """Singleton proxy for `with pv.sidebar:` and direct sidebar calls."""

    def _get_sidebar_container(self) -> Container:
        ctx = get_current_context()
        return ctx.sidebar_container

    def __enter__(self) -> Container:
        container = self._get_sidebar_container()
        ctx = get_current_context()
        ctx.container_stack.append(container)
        return container

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        ctx = get_current_context()
        if ctx.container_stack and ctx.container_stack[-1] is self._get_sidebar_container():
            ctx.container_stack.pop()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_sidebar_container(), name)


# Global singleton sidebar proxy
sidebar = SidebarProxy()
