"""Framed card grouping surfaces and containers."""

from __future__ import annotations

from pyview.components.base import Container
from pyview.core.context import get_current_context


class CardContainer(Container):
    """Represents a framed grouping surface card."""
    pass


def card(
    title: str | None = None,
    key: str | None = None,
) -> CardContainer:
    """Create a framed visual grouping card container."""
    ctx = get_current_context()
    card_id = ctx.get_widget_id("card", key)

    card_container = CardContainer(
        id=card_id,
        type="card",
        props={"title": str(title) if title is not None else None},
    )

    ctx.register_element(card_container)
    return card_container


def container(key: str | None = None) -> CardContainer:
    """Create a generic container grouping surface."""
    return card(title=None, key=key)
