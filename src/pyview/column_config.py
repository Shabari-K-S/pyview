"""Compatibility shim for pyview.column_config (moved to pyview.components.data.column_config)."""

from pyview.components.data.column_config import (
    CheckboxColumn,
    Column,
    LinkColumn,
    NumberColumn,
    ProgressColumn,
    SelectboxColumn,
    TextColumn,
)

__all__ = [
    "Column",
    "TextColumn",
    "NumberColumn",
    "CheckboxColumn",
    "SelectboxColumn",
    "ProgressColumn",
    "LinkColumn",
]
