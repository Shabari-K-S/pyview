"""Batched form container and execution boundaries."""

from __future__ import annotations

from pyview.components.base import Container
from pyview.core.context import get_current_context


class FormContainer(Container):
    """Represents a batched form container."""

    def form_submit_button(self, label: str = "Submit", key: str | None = None) -> bool:
        with self:
            from pyview.components.inputs.buttons import form_submit_button
            return form_submit_button(label, key=key)


def form(
    key: str,
    clear_on_submit: bool = False,
) -> FormContainer:
    """Create a batched form container.

    Widgets rendered inside a form do not trigger automatic script reruns when their
    values change. Instead, changes are batched client-side until `pv.form_submit_button`
    is clicked.
    """
    if not key or not str(key).strip():
        raise ValueError("form key cannot be empty.")

    ctx = get_current_context()
    form_id = f"user_{key}"
    form_container = FormContainer(
        id=form_id,
        type="form",
        props={"form_id": form_id, "clear_on_submit": clear_on_submit},
    )
    ctx.register_element(form_container)
    return form_container
