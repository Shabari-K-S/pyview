"""CinematicStudio — Multimedia & Creative Asset Hub.

Interactive PyView showcase for media elements: images, galleries,
custom audio player, video streams (HTML5 & YouTube embeds), brand logo, and PDF documents.
"""

import pyview as pv

# Sidebar Branding Logo
pv.logo("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&auto=format&fit=crop&q=60", link="https://github.com")

with pv.sidebar:
    pv.title("🎨 Studio Controls")
    pv.write("Configure studio asset layout and audio-visual playback settings.")
    selected_resolution = pv.selectbox("Target Resolution", ["4K Ultra HD (3840x2160)", "1080p Full HD", "720p HD"], index=0)
    enable_autoplay = pv.toggle("Auto-Play Media Previews", value=False)
    gallery_layout = pv.segmented_control("Gallery Mode", ["Grid", "Single Hero"], default="Grid")

pv.title("🎬 CinematicStudio — Creative Asset Hub")
pv.write("Enterprise media asset management interface with native image galleries, audio waveforms, video embeds, and interactive PDF documents.")

tab_images, tab_video, tab_audio, tab_pdf = pv.tabs([
    "🖼️ Image Galleries",
    "🎥 Video & Stream Player",
    "🎧 Audio & Voice Tracks",
    "📄 Document & PDF Viewer",
])

with tab_images:
    pv.header("1. High-Resolution Visual Gallery")
    
    if gallery_layout == "Grid":
        pv.write("Interactive responsive gallery grid with dark-mode frame cards:")
        pv.image(
            [
                "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=800&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=800&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=800&auto=format&fit=crop&q=80",
            ],
            caption=[
                "Cyberpunk Neon Corridor • Rendered with Blender Cycles",
                "Abstract Liquid Gradients • 8K High Dynamic Range",
                "Geometric Prisms • Optical Dispersion Study",
            ],
        )
    else:
        pv.image(
            "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=1200&auto=format&fit=crop&q=80",
            caption="Cyberpunk Neon Corridor • Ultra HD Featured Hero Asset",
            width=800,
        )

with tab_video:
    pv.header("2. Video Player & External Stream Embeds")
    pv.write("Supports direct MP4/WebM video feeds and **automatic detection of YouTube & Vimeo embeds**.")

    col1, col2 = pv.columns(2)
    with col1:
        pv.write("**HTML5 Video Sample (Direct MP4 URL):**")
        pv.video(
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            autoplay=enable_autoplay,
            loop=True,
        )
    with col2:
        pv.write("**Embedded YouTube Stream (Auto-parsed embed URL):**")
        pv.video(
            "https://www.youtube.com/watch?v=L_LUpnjgPso",
            autoplay=enable_autoplay,
        )

with tab_audio:
    pv.header("3. Soundtracks & Audio Streams")
    pv.write("Integrated HTML5 audio player supporting MP3, WAV, OGG, and in-memory byte buffers.")

    col_a, col_b = pv.columns(2)
    with col_a:
        pv.metric("Track Title", "Ambient Synthwave", "128 BPM")
        pv.audio(
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
            format="audio/mp3",
            loop=True,
        )
    with col_b:
        pv.metric("Format & Codec", "Stereo 44.1 kHz", "320 kbps")
        pv.audio(
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
            format="audio/mp3",
        )

with tab_pdf:
    pv.header("4. Interactive PDF Document Viewer")
    pv.write("Embedded PDF document canvas with native zoom, pan, and page navigation.")

    pv.pdf(
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        height=480,
    )
