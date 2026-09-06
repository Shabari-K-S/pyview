"""Page configuration settings (title, favicon, layout mode) for PyView."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from pyview.core.context import get_current_context


@dataclass
class PageConfig:
    """Represents browser page metadata and layout configuration."""

    page_title: str | None = None
    page_icon: str | None = None
    layout: Literal["centered", "wide"] = "centered"
    initial_sidebar_state: Literal["auto", "expanded", "collapsed"] = "auto"
    menu_items: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_title": self.page_title,
            "page_icon": self.page_icon,
            "layout": self.layout,
            "initial_sidebar_state": self.initial_sidebar_state,
            "menu_items": self.menu_items,
        }


def set_page_config(
    page_title: str | None = None,
    page_icon: str | None = None,
    layout: Literal["centered", "wide"] = "centered",
    initial_sidebar_state: Literal["auto", "expanded", "collapsed"] = "auto",
    menu_items: dict[str, Any] | None = None,
) -> None:
    """Configure browser document title, favicon, and viewport layout width.

    `layout` must be either "centered" (default, fixed readable width) or "wide" (full viewport width).
    `initial_sidebar_state` can be "auto", "expanded", or "collapsed".
    """
    if layout not in ("centered", "wide"):
        raise ValueError(f"layout must be 'centered' or 'wide', got '{layout}'")

    if initial_sidebar_state not in ("auto", "expanded", "collapsed"):
        raise ValueError(
            f"initial_sidebar_state must be 'auto', 'expanded', or 'collapsed', got '{initial_sidebar_state}'"
        )

    ctx = get_current_context()
    ctx.page_config = PageConfig(
        page_title=str(page_title) if page_title is not None else None,
        page_icon=str(page_icon) if page_icon is not None else None,
        layout=layout,
        initial_sidebar_state=initial_sidebar_state,
        menu_items=menu_items or {},
    )
