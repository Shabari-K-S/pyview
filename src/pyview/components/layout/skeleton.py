"""Shimmering skeleton placeholder loader."""

from __future__ import annotations

from pyview.components.base import Container
from pyview.core.context import get_current_context


class SkeletonContainer(Container):
    """Represents a shimmering placeholder skeleton block."""
    pass


def skeleton(
    height: int | str | None = None,
    width: int | str | None = None,
    key: str | None = None,
) -> SkeletonContainer:
    """Render a shimmering placeholder skeleton while content is loading.

    Can be used standalone or as a context manager:
    ```python
    with pv.skeleton(height=200):
        # placeholder scope
    ```
    """
    ctx = get_current_context()
    skeleton_id = ctx.get_widget_id("skeleton", key)

    h_str = f"{height}px" if isinstance(height, (int, float)) else str(height) if height else "120px"
    w_str = f"{width}px" if isinstance(width, (int, float)) else str(width) if width else "100%"

    skeleton_container = SkeletonContainer(
        id=skeleton_id,
        type="skeleton",
        props={"height": h_str, "width": w_str},
    )
    ctx.register_element(skeleton_container)
    return skeleton_container
