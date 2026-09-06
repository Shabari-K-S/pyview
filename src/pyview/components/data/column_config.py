"""Column configuration classes for PyView dataframes and data editors."""

from typing import Any, Dict, List, Optional, Union


class Column:
    """Base column configuration."""

    def __init__(
        self,
        label: Optional[str] = None,
        width: Optional[Union[int, str]] = None,
        help: Optional[str] = None,
        disabled: bool = False,
        required: bool = False,
    ):
        self.label = label
        self.width = width
        self.help = help
        self.disabled = disabled
        self.required = required

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "text",
            "label": self.label,
            "width": self.width,
            "help": self.help,
            "disabled": self.disabled,
            "required": self.required,
        }


class TextColumn(Column):
    """Configuration for standard text columns."""

    def __init__(
        self,
        label: Optional[str] = None,
        width: Optional[Union[int, str]] = None,
        help: Optional[str] = None,
        disabled: bool = False,
        required: bool = False,
        max_chars: Optional[int] = None,
        default: Optional[str] = None,
    ):
        super().__init__(label=label, width=width, help=help, disabled=disabled, required=required)
        self.max_chars = max_chars
        self.default = default

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["type"] = "text"
        d["max_chars"] = self.max_chars
        d["default"] = self.default
        return d


class NumberColumn(Column):
    """Configuration for numeric columns with formatting and boundary limits."""

    def __init__(
        self,
        label: Optional[str] = None,
        width: Optional[Union[int, str]] = None,
        help: Optional[str] = None,
        disabled: bool = False,
        required: bool = False,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        step: Optional[Union[int, float]] = None,
        format: Optional[str] = None,
        default: Optional[Union[int, float]] = None,
    ):
        super().__init__(label=label, width=width, help=help, disabled=disabled, required=required)
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.format = format
        self.default = default

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["type"] = "number"
        d["min_value"] = self.min_value
        d["max_value"] = self.max_value
        d["step"] = self.step
        d["format"] = self.format
        d["default"] = self.default
        return d


class CheckboxColumn(Column):
    """Configuration for boolean checkbox columns."""

    def __init__(
        self,
        label: Optional[str] = None,
        width: Optional[Union[int, str]] = None,
        help: Optional[str] = None,
        disabled: bool = False,
        required: bool = False,
        default: bool = False,
    ):
        super().__init__(label=label, width=width, help=help, disabled=disabled, required=required)
        self.default = default

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["type"] = "checkbox"
        d["default"] = self.default
        return d


class SelectboxColumn(Column):
    """Configuration for dropdown select columns."""

    def __init__(
        self,
        label: Optional[str] = None,
        width: Optional[Union[int, str]] = None,
        help: Optional[str] = None,
        disabled: bool = False,
        required: bool = False,
        options: Optional[List[Any]] = None,
        default: Optional[Any] = None,
    ):
        super().__init__(label=label, width=width, help=help, disabled=disabled, required=required)
        self.options = options or []
        self.default = default

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["type"] = "selectbox"
        d["options"] = self.options
        d["default"] = self.default
        return d


class ProgressColumn(Column):
    """Configuration for in-cell visual progress bar columns."""

    def __init__(
        self,
        label: Optional[str] = None,
        width: Optional[Union[int, str]] = None,
        help: Optional[str] = None,
        min_value: Union[int, float] = 0,
        max_value: Union[int, float] = 100,
        format: Optional[str] = "%d%%",
    ):
        super().__init__(label=label, width=width, help=help, disabled=True, required=False)
        self.min_value = min_value
        self.max_value = max_value
        self.format = format

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["type"] = "progress"
        d["min_value"] = self.min_value
        d["max_value"] = self.max_value
        d["format"] = self.format
        return d


class LinkColumn(Column):
    """Configuration for clickable hyperlink columns."""

    def __init__(
        self,
        label: Optional[str] = None,
        width: Optional[Union[int, str]] = None,
        help: Optional[str] = None,
        disabled: bool = True,
        display_text: Optional[str] = None,
    ):
        super().__init__(label=label, width=width, help=help, disabled=disabled, required=False)
        self.display_text = display_text

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["type"] = "link"
        d["display_text"] = self.display_text
        return d
