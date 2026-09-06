"""Compatibility shim for pyview.widgets (moved to pyview.components subpackages)."""

from pyview.components.content.json_viewer import json
from pyview.components.content.text import header, title, write
from pyview.components.data.data_editor import data_editor
from pyview.components.data.dataframe import dataframe
from pyview.components.data.table import table
from pyview.components.inputs.boolean import checkbox, toggle
from pyview.components.inputs.buttons import (
    button,
    download_button,
    form_submit_button,
    link_button,
)
from pyview.components.inputs.feedback import feedback
from pyview.components.inputs.media import color_picker, file_uploader
from pyview.components.inputs.numeric import number_input, select_slider, slider
from pyview.components.inputs.selection import (
    multiselect,
    pills,
    radio,
    segmented_control,
    selectbox,
)
from pyview.components.inputs.temporal import date_input, time_input
from pyview.components.inputs.text import chat_input, text_area, text_input
from pyview.components.status.alerts import (
    divider,
    error,
    info,
    metric,
    success,
    warning,
)
from pyview.components.status.celebrations import balloons, snow
from pyview.components.status.exception import exception
from pyview.components.status.progress import ProgressElement, progress
from pyview.components.status.spinner import SpinnerContext, spinner
from pyview.components.status.toasts import toast

__all__ = [
    "title",
    "header",
    "write",
    "button",
    "download_button",
    "link_button",
    "form_submit_button",
    "text_input",
    "text_area",
    "chat_input",
    "checkbox",
    "toggle",
    "slider",
    "select_slider",
    "number_input",
    "selectbox",
    "multiselect",
    "radio",
    "segmented_control",
    "pills",
    "date_input",
    "time_input",
    "color_picker",
    "file_uploader",
    "feedback",
    "table",
    "dataframe",
    "data_editor",
    "json",
    "progress",
    "ProgressElement",
    "spinner",
    "SpinnerContext",
    "toast",
    "balloons",
    "snow",
    "exception",
    "success",
    "info",
    "warning",
    "error",
    "divider",
    "metric",
]
