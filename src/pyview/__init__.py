"""PyView: A lightweight, pure-Python reactive web framework."""

from pyview.components.data import column_config
from pyview.components.data.column_config import (
    CheckboxColumn,
    Column,
    LinkColumn,
    NumberColumn,
    ProgressColumn,
    SelectboxColumn,
    TextColumn,
)
from pyview.components.data.data_editor import data_editor
from pyview.components.data.dataframe import dataframe
from pyview.components.data.table import table
from pyview.components.content.json_viewer import json
from pyview.components.content.text import header, title, write
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
from pyview.components.layout.card import CardContainer, card, container
from pyview.components.layout.columns import ColumnContainer, columns
from pyview.components.layout.expander import ExpanderContainer, expander
from pyview.components.layout.form import FormContainer, form
from pyview.components.layout.sidebar import SidebarProxy, sidebar
from pyview.components.layout.skeleton import SkeletonContainer, skeleton
from pyview.components.layout.status import StatusContainer, status
from pyview.components.layout.tabs import TabContainer, tabs
from pyview.components.media import audio, image, logo, pdf, video
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
from pyview.core.cache import cache_data, cache_resource
from pyview.core.context import (
    ExecutionContext,
    get_current_context,
    reset_current_context,
    set_current_context,
)
from pyview.core.flow import RerunException, StopException, rerun, stop
from pyview.core.page_config import PageConfig, set_page_config
from pyview.core.query_params import QueryParamsProxy, query_params
from pyview.core.runtime import (
    ScriptRunner,
    Session,
    SessionManager,
    execute_session_run,
)
from pyview.core.state import SessionState, session_state
from pyview.server.uploads import UploadedFile

__version__ = "0.1.0"
__all__ = [
    # State & Context
    "session_state",
    "SessionState",
    "ExecutionContext",
    "get_current_context",
    "set_current_context",
    "reset_current_context",
    # Execution Flow & Application Logic
    "rerun",
    "stop",
    "RerunException",
    "StopException",
    "cache_data",
    "cache_resource",
    "set_page_config",
    "PageConfig",
    "query_params",
    "QueryParamsProxy",
    # Runtime & Sessions
    "Session",
    "SessionManager",
    "ScriptRunner",
    "execute_session_run",
    # Typography & Content
    "title",
    "header",
    "write",
    "json",
    # Value & Form Controls
    "button",
    "text_input",
    "text_area",
    "checkbox",
    "toggle",
    "radio",
    "multiselect",
    "segmented_control",
    "pills",
    "select_slider",
    "color_picker",
    "feedback",
    "slider",
    "number_input",
    "selectbox",
    "date_input",
    "time_input",
    "download_button",
    "link_button",
    "chat_input",
    "file_uploader",
    "UploadedFile",
    # Tabular Data & Data Editor
    "table",
    "dataframe",
    "data_editor",
    "column_config",
    "Column",
    "TextColumn",
    "NumberColumn",
    "CheckboxColumn",
    "SelectboxColumn",
    "ProgressColumn",
    "LinkColumn",
    # Media Elements
    "image",
    "audio",
    "video",
    "logo",
    "pdf",
    # Status, Progress & Celebrations
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
    # Layout Containers, Skeletons & Forms
    "columns",
    "ColumnContainer",
    "tabs",
    "TabContainer",
    "expander",
    "ExpanderContainer",
    "card",
    "CardContainer",
    "container",
    "status",
    "StatusContainer",
    "skeleton",
    "SkeletonContainer",
    "form",
    "FormContainer",
    "sidebar",
    "SidebarProxy",
]
