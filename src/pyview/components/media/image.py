"""Image display element supporting URLs, files, bytes, PIL Images, and NumPy arrays."""

from __future__ import annotations

from typing import Any, Sequence
from pyview.components.media.utils import process_image_to_data_url
from pyview.core.context import get_current_context


def image(
    image: Any,
    caption: str | Sequence[str] | None = None,
    width: int | str | None = None,
    use_container_width: bool = True,
    clamp: bool = False,
    channels: str = "RGB",
    output_format: str = "auto",
    key: str | None = None,
) -> None:
    """Display an image or a gallery grid of images.

    `image` can be:
    - URL string (e.g. "https://...", "data:image/...")
    - Local file path (`str` or `Path`)
    - Raw image `bytes` or `io.BytesIO`
    - PIL `Image.Image` object
    - NumPy image array `(H, W)`, `(H, W, 3)`, or `(H, W, 4)`
    - A list/tuple of any of the above (renders a responsive image gallery)
    """
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("image", key)

    is_list = isinstance(image, (list, tuple))
    image_list = list(image) if is_list else [image]

    # Process captions
    if caption is None:
        caption_list: list[str | None] = [None] * len(image_list)
    elif isinstance(caption, (list, tuple)):
        caption_list = [str(c) if c is not None else None for c in caption]
        # Pad caption list if shorter than image list
        while len(caption_list) < len(image_list):
            caption_list.append(None)
    else:
        caption_list = [str(caption)] + [None] * (len(image_list) - 1)

    processed_items: list[dict[str, Any]] = []
    for img_item, cap in zip(image_list, caption_list):
        src = process_image_to_data_url(img_item, output_format=output_format)
        processed_items.append({
            "src": src,
            "caption": cap,
        })

    width_str = f"{width}px" if isinstance(width, (int, float)) else (str(width) if width else None)

    ctx.register_element({
        "type": "image",
        "id": widget_id,
        "props": {
            "items": processed_items,
            "is_gallery": is_list and len(processed_items) > 1,
            "width": width_str,
            "use_container_width": bool(use_container_width),
        },
    })
