"""Multi-column grid layout with proportional column weights."""

from __future__ import annotations

from typing import Sequence
from pyview.components.base import Container
from pyview.core.context import get_current_context


class ColumnContainer(Container):
    """Represents an individual column within a columns layout."""
    pass


def columns(
    spec: int | Sequence[int | float],
    key: str | None = None,
) -> list[ColumnContainer]:
    """Create a responsive multi-column layout.

    `spec` can be an integer (e.g. 3) or a sequence of column weights (e.g. [2, 1, 1]).
    Returns a list of ColumnContainer objects that can be used with `with col:`.
    """
    ctx = get_current_context()

    if isinstance(spec, int):
        if spec <= 0:
            raise ValueError(f"columns count must be greater than 0, got {spec}")
        weights = [1] * spec
    else:
        weights = list(spec)
        if not weights or len(weights) == 0:
            raise ValueError("columns weight sequence cannot be empty.")
        if any(w <= 0 for w in weights):
            raise ValueError(f"column weights must be positive numbers, got {weights}")

    columns_id = ctx.get_widget_id("columns", key)
    columns_container = Container(
        id=columns_id,
        type="columns",
        props={"spec": weights},
    )

    col_containers: list[ColumnContainer] = []
    for i, w in enumerate(weights):
        col_id = f"{columns_id}.col_{i}"
        col = ColumnContainer(
            id=col_id,
            type="column",
            props={"weight": w, "index": i},
        )
        col_containers.append(col)
        columns_container.children.append(col)

    ctx.register_element(columns_container)
    return col_containers
