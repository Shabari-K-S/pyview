"""HTML5 audio player element supporting URLs, audio files, and raw bytes."""

from __future__ import annotations

from typing import Any
from pyview.components.media.utils import process_audio_to_data_url
from pyview.core.context import get_current_context


def audio(
    data: Any,
    format: str = "audio/wav",
    start_time: int = 0,
    end_time: int | None = None,
    loop: bool = False,
    autoplay: bool = False,
    key: str | None = None,
) -> None:
    """Display an audio player.

    `data` can be:
    - URL string (e.g. "https://...", "data:audio/...")
    - Local audio file path (`str` or `Path`)
    - Raw audio `bytes` or `io.BytesIO`
    """
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("audio", key)

    src = process_audio_to_data_url(data, format=format)

    ctx.register_element({
        "type": "audio",
        "id": widget_id,
        "props": {
            "src": src,
            "format": str(format),
            "start_time": int(start_time),
            "end_time": int(end_time) if end_time is not None else None,
            "loop": bool(loop),
            "autoplay": bool(autoplay),
        },
    })
