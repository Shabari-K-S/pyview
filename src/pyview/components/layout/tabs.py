"""Tabbed navigation switcher container."""

from __future__ import annotations

from typing import Sequence
from pyview.components.base import Container
from pyview.core.context import get_current_context


class TabContainer(Container):
    """Represents an individual tab pane within a tabs container."""
    pass


def tabs(
    tab_names: Sequence[str],
    key: str | None = None,
) -> list[TabContainer]:
    """Create a tabbed navigation container.

    All tab contents are fully executed top-to-bottom on the backend during each rerun.
    Frontend toggles CSS visibility client-side with zero WebSocket roundtrips on tab switch.
    """
    if not tab_names or len(tab_names) == 0:
        raise ValueError("tabs sequence cannot be empty.")

    ctx = get_current_context()
    tabs_id = ctx.get_widget_id("tabs", key)

    tab_labels = [str(name) for name in tab_names]
    tabs_container = Container(
        id=tabs_id,
        type="tabs",
        props={"tab_names": tab_labels},
    )

    tab_containers: list[TabContainer] = []
    for i, name in enumerate(tab_labels):
        tab_id = f"{tabs_id}.tab_{i}"
        tab = TabContainer(
            id=tab_id,
            type="tab",
            props={"label": name, "index": i},
        )
        tab_containers.append(tab)
        tabs_container.children.append(tab)

    ctx.register_element(tabs_container)
    return tab_containers
