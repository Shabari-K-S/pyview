"""Base container class and context manager protocol for PyView components."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Sequence

if TYPE_CHECKING:
    import datetime


@dataclass
class Container:
    """Base layout container supporting Python `with` context manager scoping."""

    id: str
    type: str
    props: dict[str, Any] = field(default_factory=dict)
    children: list[dict[str, Any] | Container] = field(default_factory=list)
    positional_counters: dict[str, int] = field(default_factory=dict)

    def __enter__(self) -> Container:
        from pyview.core.context import get_current_context
        ctx = get_current_context()
        ctx.container_stack.append(self)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        from pyview.core.context import get_current_context
        ctx = get_current_context()
        if ctx.container_stack and ctx.container_stack[-1] is self:
            ctx.container_stack.pop()

    def to_dict(self) -> dict[str, Any]:
        """Recursively serialize the container and its nested children to JSON."""
        return {
            "type": self.type,
            "id": self.id,
            "props": self.props,
            "children": [
                child.to_dict() if hasattr(child, "to_dict") else child
                for child in self.children
            ],
        }

    # Widget convenience methods on container instance (e.g. col.button(...), sb.title(...))
    def title(self, text: str, key: str | None = None) -> None:
        with self:
            from pyview.components.content.text import title
            title(text, key=key)

    def header(self, text: str, key: str | None = None) -> None:
        with self:
            from pyview.components.content.text import header
            header(text, key=key)

    def write(self, *args: Any, key: str | None = None) -> None:
        with self:
            from pyview.components.content.text import write
            write(*args, key=key)

    def button(self, label: str, key: str | None = None) -> bool:
        with self:
            from pyview.components.inputs.buttons import button
            return button(label, key=key)

    def text_input(
        self,
        label: str,
        value: str = "",
        key: str | None = None,
        placeholder: str = "",
        type: str = "text",
    ) -> str:
        with self:
            from pyview.components.inputs.text import text_input
            return text_input(label, value=value, key=key, placeholder=placeholder, type=type)

    def text_area(
        self,
        label: str,
        value: str = "",
        height: int = 120,
        placeholder: str = "",
        key: str | None = None,
    ) -> str:
        with self:
            from pyview.components.inputs.text import text_area
            return text_area(label, value=value, height=height, placeholder=placeholder, key=key)

    def checkbox(self, label: str, value: bool = False, key: str | None = None) -> bool:
        with self:
            from pyview.components.inputs.boolean import checkbox
            return checkbox(label, value=value, key=key)

    def toggle(self, label: str, value: bool = False, key: str | None = None) -> bool:
        with self:
            from pyview.components.inputs.boolean import toggle
            return toggle(label, value=value, key=key)

    def slider(
        self,
        label: str,
        min_value: int | float = 0,
        max_value: int | float = 100,
        value: int | float | None = None,
        step: int | float | None = None,
        key: str | None = None,
    ) -> int | float:
        with self:
            from pyview.components.inputs.numeric import slider
            return slider(label, min_value=min_value, max_value=max_value, value=value, step=step, key=key)

    def number_input(
        self,
        label: str,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        value: int | float | None = None,
        step: int | float | None = None,
        key: str | None = None,
    ) -> int | float:
        with self:
            from pyview.components.inputs.numeric import number_input
            return number_input(label, min_value=min_value, max_value=max_value, value=value, step=step, key=key)

    def selectbox(
        self,
        label: str,
        options: Sequence[Any],
        index: int = 0,
        key: str | None = None,
    ) -> Any:
        with self:
            from pyview.components.inputs.selection import selectbox
            return selectbox(label, options=options, index=index, key=key)

    def metric(
        self,
        label: str,
        value: Any,
        delta: Any = None,
        delta_color: str = "normal",
        key: str | None = None,
    ) -> None:
        with self:
            from pyview.components.status.alerts import metric
            metric(label, value=value, delta=delta, delta_color=delta_color, key=key)

    def success(self, text: str, icon: str = "✅", key: str | None = None) -> None:
        with self:
            from pyview.components.status.alerts import success
            success(text, icon=icon, key=key)

    def info(self, text: str, icon: str = "ℹ️", key: str | None = None) -> None:
        with self:
            from pyview.components.status.alerts import info
            info(text, icon=icon, key=key)

    def warning(self, text: str, icon: str = "⚠️", key: str | None = None) -> None:
        with self:
            from pyview.components.status.alerts import warning
            warning(text, icon=icon, key=key)

    def error(self, text: str, icon: str = "❌", key: str | None = None) -> None:
        with self:
            from pyview.components.status.alerts import error
            error(text, icon=icon, key=key)

    def divider(self, key: str | None = None) -> None:
        with self:
            from pyview.components.status.alerts import divider
            divider(key=key)

    def image(
        self,
        image: Any,
        caption: str | Sequence[str] | None = None,
        width: int | str | None = None,
        use_container_width: bool = True,
        clamp: bool = False,
        channels: str = "RGB",
        output_format: str = "auto",
        key: str | None = None,
    ) -> None:
        with self:
            from pyview.components.media.image import image as img_fn
            img_fn(
                image,
                caption=caption,
                width=width,
                use_container_width=use_container_width,
                clamp=clamp,
                channels=channels,
                output_format=output_format,
                key=key,
            )

    def audio(
        self,
        data: Any,
        format: str = "audio/wav",
        start_time: int = 0,
        end_time: int | None = None,
        loop: bool = False,
        autoplay: bool = False,
        key: str | None = None,
    ) -> None:
        with self:
            from pyview.components.media.audio import audio as audio_fn
            audio_fn(
                data,
                format=format,
                start_time=start_time,
                end_time=end_time,
                loop=loop,
                autoplay=autoplay,
                key=key,
            )

    def video(
        self,
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
        with self:
            from pyview.components.media.video import video as video_fn
            video_fn(
                data,
                format=format,
                start_time=start_time,
                end_time=end_time,
                loop=loop,
                autoplay=autoplay,
                muted=muted,
                subtitles=subtitles,
                key=key,
            )

    def logo(
        self,
        image: Any,
        link: str | None = None,
        icon_image: Any = None,
        key: str | None = None,
    ) -> None:
        with self:
            from pyview.components.media.logo import logo as logo_fn
            logo_fn(image, link=link, icon_image=icon_image, key=key)

    def pdf(
        self,
        data: Any,
        height: int | str = 500,
        width: int | str | None = None,
        key: str | None = None,
    ) -> None:
        with self:
            from pyview.components.media.pdf import pdf as pdf_fn
            pdf_fn(data, height=height, width=width, key=key)
