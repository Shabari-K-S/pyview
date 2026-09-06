"""Sidebar and header brand logo component."""

from __future__ import annotations

from typing import Any
from pyview.components.media.utils import process_image_to_data_url
from pyview.core.context import get_current_context


def logo(
    image: Any,
    link: str | None = None,
    icon_image: Any = None,
    key: str | None = None,
) -> None:
    """Display a brand logo in the sidebar header.

    `image`: The primary logo image (shown when the sidebar is open).
    `icon_image`: An optional smaller icon shown when the sidebar is collapsed.
    `link`: An optional URL to navigate to when the logo is clicked.
    """
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("logo", key)

    main_src = process_image_to_data_url(image)
    icon_src = process_image_to_data_url(icon_image) if icon_image else main_src

    # Register in sidebar container if present, else root
    logo_el = {
        "type": "logo",
        "id": widget_id,
        "props": {
            "image": main_src,
            "icon_image": icon_src,
            "link": str(link) if link else None,
        },
    }

    # Prepend or register to sidebar container
    if ctx.sidebar_container:
        ctx.sidebar_container.children.insert(0, logo_el)
    else:
        ctx.register_element(logo_el)
