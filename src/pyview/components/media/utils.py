"""Media processing, MIME-type inference, and embed parsing utilities for PyView."""

from __future__ import annotations

import base64
import io
import mimetypes
from pathlib import Path
import re
import threading
from typing import Any

# Thread-safe in-memory cache for media file reads & Base64 conversions:
# Key: (media_type, resolved_path, mtime, size, extra_format) -> data_uri
_FILE_MEDIA_CACHE: dict[tuple[str, str, float, int, str], Any] = {}
_MAX_MEDIA_CACHE_ENTRIES = 256
_media_cache_lock = threading.Lock()


def _get_cached_file_media(media_type: str, path: Path, extra_format: str = "") -> Any | None:
    try:
        stat = path.stat()
        key = (media_type, str(path.resolve()), stat.st_mtime, stat.st_size, extra_format)
        with _media_cache_lock:
            return _FILE_MEDIA_CACHE.get(key)
    except Exception:
        return None


def _put_cached_file_media(media_type: str, path: Path, result: Any, extra_format: str = "") -> None:
    try:
        stat = path.stat()
        key = (media_type, str(path.resolve()), stat.st_mtime, stat.st_size, extra_format)
        with _media_cache_lock:
            if len(_FILE_MEDIA_CACHE) >= _MAX_MEDIA_CACHE_ENTRIES:
                _FILE_MEDIA_CACHE.pop(next(iter(_FILE_MEDIA_CACHE)), None)
            _FILE_MEDIA_CACHE[key] = result
    except Exception:
        pass


def parse_video_embed_url(url: str) -> tuple[str | None, str]:
    """Inspect a URL string to determine if it is YouTube or Vimeo and return an embed URL.

    Returns (embed_url, embed_type) where embed_type is 'youtube', 'vimeo', or 'direct'.
    """
    if not isinstance(url, str):
        return None, "direct"

    clean_url = url.strip()

    # YouTube patterns:
    # - https://www.youtube.com/watch?v=VIDEO_ID
    # - https://youtu.be/VIDEO_ID
    # - https://www.youtube.com/embed/VIDEO_ID
    # - https://www.youtube.com/shorts/VIDEO_ID
    yt_match = re.search(
        r"(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})",
        clean_url,
    )
    if yt_match:
        video_id = yt_match.group(1)
        return f"https://www.youtube.com/embed/{video_id}?autoplay=0&rel=0", "youtube"

    # Vimeo patterns:
    # - https://vimeo.com/VIDEO_ID
    # - https://player.vimeo.com/video/VIDEO_ID
    vimeo_match = re.search(r"vimeo\.com\/(?:video\/)?([0-9]+)", clean_url)
    if vimeo_match:
        video_id = vimeo_match.group(1)
        return f"https://player.vimeo.com/video/{video_id}", "vimeo"

    return None, "direct"


def process_image_to_data_url(image_data: Any, output_format: str = "auto") -> str:
    """Convert an image (URL string, file path, bytes, BytesIO, PIL Image, or NumPy array) to a valid image source URL or Data URI."""
    if image_data is None:
        return ""

    # 1. URL string (HTTP/HTTPS or already a Data URI)
    if isinstance(image_data, str):
        stripped = image_data.strip()
        if stripped.startswith(("http://", "https://", "data:image/")):
            return stripped

        # Local file path
        path = Path(stripped)
        if path.exists() and path.is_file():
            cached = _get_cached_file_media("image", path, output_format)
            if cached is not None:
                return cached
            mime, _ = mimetypes.guess_type(str(path))
            mime = mime or "image/png"
            raw_bytes = path.read_bytes()
            b64 = base64.b64encode(raw_bytes).decode("ascii")
            uri = f"data:{mime};base64,{b64}"
            _put_cached_file_media("image", path, uri, output_format)
            return uri
        return stripped

    # 2. Path object
    if isinstance(image_data, Path):
        if image_data.exists() and image_data.is_file():
            cached = _get_cached_file_media("image", image_data, output_format)
            if cached is not None:
                return cached
            mime, _ = mimetypes.guess_type(str(image_data))
            mime = mime or "image/png"
            raw_bytes = image_data.read_bytes()
            b64 = base64.b64encode(raw_bytes).decode("ascii")
            uri = f"data:{mime};base64,{b64}"
            _put_cached_file_media("image", image_data, uri, output_format)
            return uri

    # 3. Raw Bytes / BytesIO
    if isinstance(image_data, (bytes, bytearray)):
        fmt = output_format if output_format != "auto" else "png"
        mime = f"image/{fmt.lower()}"
        b64 = base64.b64encode(image_data).decode("ascii")
        return f"data:{mime};base64,{b64}"

    if isinstance(image_data, io.BytesIO):
        raw = image_data.getvalue()
        fmt = output_format if output_format != "auto" else "png"
        mime = f"image/{fmt.lower()}"
        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{b64}"

    # 4. PIL Image
    pil_type = type(image_data).__name__
    pil_module = getattr(type(image_data), "__module__", "")
    if "PIL" in pil_module or pil_type == "Image":
        try:
            buf = io.BytesIO()
            save_fmt = "PNG" if output_format == "auto" else output_format.upper()
            image_data.save(buf, format=save_fmt)
            raw = buf.getvalue()
            mime = f"image/{save_fmt.lower()}"
            b64 = base64.b64encode(raw).decode("ascii")
            return f"data:{mime};base64,{b64}"
        except Exception:
            pass

    # 5. NumPy array (H, W), (H, W, 3), (H, W, 4)
    numpy_module = getattr(type(image_data), "__module__", "")
    if "numpy" in numpy_module or hasattr(image_data, "shape"):
        try:
            from PIL import Image as PILImage
            import numpy as np

            arr = np.array(image_data)
            # Normalize float [0.0, 1.0] to uint8 [0, 255]
            if arr.dtype.kind == "f":
                arr = (np.clip(arr, 0.0, 1.0) * 255).astype(np.uint8)
            else:
                arr = np.clip(arr, 0, 255).astype(np.uint8)

            img = PILImage.fromarray(arr)
            buf = io.BytesIO()
            save_fmt = "PNG" if output_format == "auto" else output_format.upper()
            img.save(buf, format=save_fmt)
            raw = buf.getvalue()
            mime = f"image/{save_fmt.lower()}"
            b64 = base64.b64encode(raw).decode("ascii")
            return f"data:{mime};base64,{b64}"
        except Exception:
            pass

    return str(image_data)


def process_audio_to_data_url(audio_data: Any, format: str = "audio/wav") -> str:
    """Convert audio data (URL, local file path, bytes, or BytesIO) to an audio URL or Data URI."""
    if audio_data is None:
        return ""

    if isinstance(audio_data, str):
        stripped = audio_data.strip()
        if stripped.startswith(("http://", "https://", "data:audio/")):
            return stripped

        path = Path(stripped)
        if path.exists() and path.is_file():
            cached = _get_cached_file_media("audio", path, format)
            if cached is not None:
                return cached
            mime, _ = mimetypes.guess_type(str(path))
            mime = mime or format or "audio/wav"
            raw_bytes = path.read_bytes()
            b64 = base64.b64encode(raw_bytes).decode("ascii")
            uri = f"data:{mime};base64,{b64}"
            _put_cached_file_media("audio", path, uri, format)
            return uri
        return stripped

    if isinstance(audio_data, Path):
        if audio_data.exists() and audio_data.is_file():
            cached = _get_cached_file_media("audio", audio_data, format)
            if cached is not None:
                return cached
            mime, _ = mimetypes.guess_type(str(audio_data))
            mime = mime or format or "audio/wav"
            raw_bytes = audio_data.read_bytes()
            b64 = base64.b64encode(raw_bytes).decode("ascii")
            uri = f"data:{mime};base64,{b64}"
            _put_cached_file_media("audio", audio_data, uri, format)
            return uri

    if isinstance(audio_data, (bytes, bytearray)):
        mime = format or "audio/wav"
        b64 = base64.b64encode(audio_data).decode("ascii")
        return f"data:{mime};base64,{b64}"

    if isinstance(audio_data, io.BytesIO):
        raw = audio_data.getvalue()
        mime = format or "audio/wav"
        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{b64}"

    return str(audio_data)


def process_video_to_data_url(video_data: Any, format: str = "video/mp4") -> tuple[str, str]:
    """Convert video data to a tuple (src_url, embed_type) where embed_type is 'youtube', 'vimeo', or 'direct'."""
    if video_data is None:
        return "", "direct"

    if isinstance(video_data, str):
        stripped = video_data.strip()
        # Check YouTube / Vimeo
        embed_url, embed_type = parse_video_embed_url(stripped)
        if embed_url:
            return embed_url, embed_type

        if stripped.startswith(("http://", "https://", "data:video/")):
            return stripped, "direct"

        path = Path(stripped)
        if path.exists() and path.is_file():
            cached = _get_cached_file_media("video", path, format)
            if cached is not None:
                return cached
            mime, _ = mimetypes.guess_type(str(path))
            mime = mime or format or "video/mp4"
            raw_bytes = path.read_bytes()
            b64 = base64.b64encode(raw_bytes).decode("ascii")
            res = (f"data:{mime};base64,{b64}", "direct")
            _put_cached_file_media("video", path, res, format)
            return res
        return stripped, "direct"

    if isinstance(video_data, Path):
        if video_data.exists() and video_data.is_file():
            cached = _get_cached_file_media("video", video_data, format)
            if cached is not None:
                return cached
            mime, _ = mimetypes.guess_type(str(video_data))
            mime = mime or format or "video/mp4"
            raw_bytes = video_data.read_bytes()
            b64 = base64.b64encode(raw_bytes).decode("ascii")
            res = (f"data:{mime};base64,{b64}", "direct")
            _put_cached_file_media("video", video_data, res, format)
            return res

    if isinstance(video_data, (bytes, bytearray)):
        mime = format or "video/mp4"
        b64 = base64.b64encode(video_data).decode("ascii")
        return f"data:{mime};base64,{b64}", "direct"

    if isinstance(video_data, io.BytesIO):
        raw = video_data.getvalue()
        mime = format or "video/mp4"
        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{b64}", "direct"

    return str(video_data), "direct"


def process_pdf_to_data_url(pdf_data: Any) -> str:
    """Convert PDF file or raw bytes to a Data URI."""
    if pdf_data is None:
        return ""

    if isinstance(pdf_data, str):
        stripped = pdf_data.strip()
        if stripped.startswith(("http://", "https://", "data:application/pdf")):
            return stripped

        path = Path(stripped)
        if path.exists() and path.is_file():
            cached = _get_cached_file_media("pdf", path)
            if cached is not None:
                return cached
            raw_bytes = path.read_bytes()
            b64 = base64.b64encode(raw_bytes).decode("ascii")
            uri = f"data:application/pdf;base64,{b64}"
            _put_cached_file_media("pdf", path, uri)
            return uri
        return stripped

    if isinstance(pdf_data, Path):
        if pdf_data.exists() and pdf_data.is_file():
            cached = _get_cached_file_media("pdf", pdf_data)
            if cached is not None:
                return cached
            raw_bytes = pdf_data.read_bytes()
            b64 = base64.b64encode(raw_bytes).decode("ascii")
            uri = f"data:application/pdf;base64,{b64}"
            _put_cached_file_media("pdf", pdf_data, uri)
            return uri

    if isinstance(pdf_data, (bytes, bytearray)):
        b64 = base64.b64encode(pdf_data).decode("ascii")
        return f"data:application/pdf;base64,{b64}"

    if isinstance(pdf_data, io.BytesIO):
        raw = pdf_data.getvalue()
        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:application/pdf;base64,{b64}"

    return str(pdf_data)
