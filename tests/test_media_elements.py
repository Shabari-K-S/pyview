"""Unit tests for PyView media elements (image, audio, video, logo, pdf)."""

import io
import pytest
from pyview.components.media.utils import (
    parse_video_embed_url,
    process_audio_to_data_url,
    process_image_to_data_url,
    process_pdf_to_data_url,
    process_video_to_data_url,
)
from pyview.core.context import ExecutionContext, reset_current_context, set_current_context
from pyview.core.runtime import Session
import pyview as pv


@pytest.fixture
def session():
    return Session(session_id="test_media_session")


def test_parse_video_embed_url():
    # YouTube watch URL
    yt_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    embed, mode = parse_video_embed_url(yt_url)
    assert mode == "youtube"
    assert "https://www.youtube.com/embed/dQw4w9WgXcQ" in embed

    # YouTube short link
    yt_short = "https://youtu.be/dQw4w9WgXcQ"
    embed, mode = parse_video_embed_url(yt_short)
    assert mode == "youtube"
    assert "https://www.youtube.com/embed/dQw4w9WgXcQ" in embed

    # Vimeo URL
    vimeo_url = "https://vimeo.com/76979871"
    embed, mode = parse_video_embed_url(vimeo_url)
    assert mode == "vimeo"
    assert "https://player.vimeo.com/video/76979871" in embed

    # Direct MP4 video URL
    direct_url = "https://www.w3schools.com/html/mov_bbb.mp4"
    embed, mode = parse_video_embed_url(direct_url)
    assert mode == "direct"
    assert embed is None


def test_image_element_url_and_bytes(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        # Single URL image
        pv.image("https://example.com/logo.png", caption="Brand Logo", width=300)
        
        # Raw bytes image
        raw_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        pv.image(raw_png, caption="Raw Byte Image")

        # Multi-image gallery
        pv.image(["https://example.com/1.png", "https://example.com/2.png"], caption=["Pic 1", "Pic 2"])

        elements = ctx.get_serialized_elements()
        assert len(elements) == 3

        # First element
        el1 = elements[0]
        assert el1["type"] == "image"
        assert el1["props"]["width"] == "300px"
        assert len(el1["props"]["items"]) == 1
        assert el1["props"]["items"][0]["src"] == "https://example.com/logo.png"
        assert el1["props"]["items"][0]["caption"] == "Brand Logo"

        # Second element (raw bytes Base64)
        el2 = elements[1]
        assert el2["props"]["items"][0]["src"].startswith("data:image/png;base64,")

        # Third element (gallery)
        el3 = elements[2]
        assert el3["props"]["is_gallery"] is True
        assert len(el3["props"]["items"]) == 2
    finally:
        reset_current_context(token)


def test_audio_element_generation(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        pv.audio("https://example.com/track.mp3", format="audio/mp3", loop=True)
        raw_wav = b"RIFF....WAVEfmt "
        pv.audio(raw_wav, format="audio/wav", start_time=15)

        elements = ctx.get_serialized_elements()
        assert len(elements) == 2

        el1 = elements[0]
        assert el1["type"] == "audio"
        assert el1["props"]["src"] == "https://example.com/track.mp3"
        assert el1["props"]["loop"] is True

        el2 = elements[1]
        assert el2["props"]["src"].startswith("data:audio/wav;base64,")
        assert el2["props"]["start_time"] == 15
    finally:
        reset_current_context(token)


def test_video_element_direct_and_youtube(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        # YouTube embed
        pv.video("https://www.youtube.com/watch?v=L_LUpnjgPso")
        # Direct video URL
        pv.video("https://example.com/movie.mp4", autoplay=True, muted=True)

        elements = ctx.get_serialized_elements()
        assert len(elements) == 2

        el_yt = elements[0]
        assert el_yt["type"] == "video"
        assert el_yt["props"]["embed_type"] == "youtube"
        assert "https://www.youtube.com/embed/L_LUpnjgPso" in el_yt["props"]["src"]

        el_direct = elements[1]
        assert el_direct["props"]["embed_type"] == "direct"
        assert el_direct["props"]["src"] == "https://example.com/movie.mp4"
        assert el_direct["props"]["autoplay"] is True
        assert el_direct["props"]["muted"] is True
    finally:
        reset_current_context(token)


def test_logo_and_pdf_elements(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        pv.logo("https://example.com/logo.svg", link="https://example.com")
        
        pdf_bytes = b"%PDF-1.4 sample pdf content"
        pv.pdf(pdf_bytes, height=600)

        elements = ctx.get_serialized_elements()
        # Sidebar container has the logo
        sb = ctx.sidebar_container
        assert len(sb.children) == 1
        assert sb.children[0]["type"] == "logo"
        assert sb.children[0]["props"]["image"] == "https://example.com/logo.svg"
        assert sb.children[0]["props"]["link"] == "https://example.com"

        # Root elements have the PDF
        assert len(elements) == 2  # sidebar + pdf
        pdf_el = elements[1]
        assert pdf_el["type"] == "pdf"
        assert pdf_el["props"]["src"].startswith("data:application/pdf;base64,")
        assert pdf_el["props"]["height"] == "600px"
    finally:
        reset_current_context(token)


def test_container_media_delegation(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        col1, col2 = pv.columns(2)
        with col1:
            col1.image("https://example.com/test.jpg")
        with col2:
            col2.audio("https://example.com/sound.mp3")

        elements = ctx.get_serialized_elements()
        assert len(elements) == 1
        cols = elements[0]
        assert cols["type"] == "columns"
        assert cols["children"][0]["children"][0]["type"] == "image"
        assert cols["children"][1]["children"][0]["type"] == "audio"
    finally:
        reset_current_context(token)


def test_media_file_caching(tmp_path, session):
    from pyview.components.media.utils import _FILE_MEDIA_CACHE, process_image_to_data_url
    test_img = tmp_path / "test.png"
    test_img.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"image_data_here")

    _FILE_MEDIA_CACHE.clear()

    uri1 = process_image_to_data_url(test_img, "png")
    assert uri1.startswith("data:image/png;base64,")
    assert len(_FILE_MEDIA_CACHE) == 1

    uri2 = process_image_to_data_url(test_img, "png")
    assert uri2 == uri1
    assert len(_FILE_MEDIA_CACHE) == 1
