"""Video player supporting video files, MP4/WebM URLs, and YouTube/Vimeo embeds."""

from __future__ import annotations

from typing import Any
from pyview.components.media.utils import process_video_to_data_url
from pyview.core.context import get_current_context


def video(
    data: Any,
    format: str = "video/mp4",
    start_time: int = 0,
    end_time: int | None = None,
    loop: bool = False,
    autoplay: bool = False,
    muted: bool = False,
    subtitles: dict[str, str] | None = None,
    key: str | None = None,
) -> None:
    """Display a video player or embedded video stream.

    `data` can be:
    - YouTube URL (e.g. "https://www.youtube.com/watch?v=...", "https://youtu.be/...")
    - Vimeo URL (e.g. "https://vimeo.com/...")
    - Direct video URL or Data URI
    - Local video file path (`str` or `Path`)
    - Raw video `bytes` or `io.BytesIO`
    """
    ctx = get_current_context()
    widget_id = ctx.get_widget_id("video", key)

    src, embed_type = process_video_to_data_url(data, format=format)

    ctx.register_element({
        "type": "video",
        "id": widget_id,
        "props": {
            "src": src,
            "embed_type": embed_type,
            "format": str(format),
            "start_time": int(start_time),
            "end_time": int(end_time) if end_time is not None else None,
            "loop": bool(loop),
            "autoplay": bool(autoplay),
            "muted": bool(muted),
            "subtitles": subtitles or {},
        },
    })
