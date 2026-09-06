import pytest
from pyview.context import ExecutionContext, reset_current_context, set_current_context
from pyview.runtime import Session
import pyview as pv


@pytest.fixture
def session():
    return Session(session_id="test_status_session")


def test_progress_bar_normalization_and_updates(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        # Float normalized to 0-100%
        prog = pv.progress(0.75, text="Processing batch...")
        elements = ctx.get_serialized_elements()
        assert len(elements) == 1
        assert elements[0]["type"] == "progress"
        assert elements[0]["props"]["value"] == 75
        assert elements[0]["props"]["text"] == "Processing batch..."

        # Live in-place progression
        prog.progress(1.0, text="Finished!")
        assert elements[0]["props"]["value"] == 100
        assert elements[0]["props"]["text"] == "Finished!"

        # Integer value
        pv.progress(42, text="Step 42 of 100", key="custom_prog")
        elements = ctx.get_serialized_elements()
        assert len(elements) == 2
        assert elements[1]["id"] == "user_custom_prog"
        assert elements[1]["props"]["value"] == 42
    finally:
        reset_current_context(token)


def test_spinner_standalone_and_context_manager(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        # Standalone
        pv.spinner("Searching records...")
        # Context manager
        with pv.spinner("Computing eigenvalues..."):
            pv.write("Step 1 done")

        elements = ctx.get_serialized_elements()
        assert any(e["type"] == "spinner" and e["props"]["text"] == "Searching records..." for e in elements)
        assert any(e["type"] == "spinner" and e["props"]["text"] == "Computing eigenvalues..." for e in elements)
        assert any(e["type"] == "write" and "Step 1 done" in str(e["props"]["content"]) for e in elements)
    finally:
        reset_current_context(token)


def test_status_container_and_state_transitions(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        with pv.status("Deploying service...", expanded=True, state="running") as status_box:
            pv.write("Building Docker container...")
            pv.write("Pushing image to registry...")
            status_box.update(label="Deployment Succeeded!", state="complete", expanded=False)

        elements = ctx.get_serialized_elements()
        assert len(elements) == 1
        el = elements[0]
        assert el["type"] == "status_container"
        assert el["props"]["label"] == "Deployment Succeeded!"
        assert el["props"]["state"] == "complete"
        assert el["props"]["expanded"] is False
        assert len(el["children"]) == 2
    finally:
        reset_current_context(token)


def test_status_invalid_state_raises_error(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        with pytest.raises(ValueError, match="state must be one of"):
            pv.status("Testing", state="invalid_state")
    finally:
        reset_current_context(token)


def test_skeleton_container_and_props(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        with pv.skeleton(height=240, width=500):
            pv.write("Loading preview...")

        elements = ctx.get_serialized_elements()
        assert len(elements) == 1
        el = elements[0]
        assert el["type"] == "skeleton"
        assert el["props"]["height"] == "240px"
        assert el["props"]["width"] == "500px"
        assert len(el["children"]) == 1
    finally:
        reset_current_context(token)


def test_toast_and_celebrations(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        pv.toast("Operation completed successfully!", icon="🚀")
        pv.balloons()
        pv.snow()

        elements = ctx.get_serialized_elements()
        assert len(elements) == 3

        toast_el = elements[0]
        assert toast_el["type"] == "toast"
        assert toast_el["props"]["body"] == "Operation completed successfully!"
        assert toast_el["props"]["icon"] == "🚀"

        balloon_el = elements[1]
        assert balloon_el["type"] == "balloons"

        snow_el = elements[2]
        assert snow_el["type"] == "snow"
    finally:
        reset_current_context(token)


def test_exception_element_formatting(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        try:
            raise ZeroDivisionError("division by zero in calculation")
        except ZeroDivisionError as e:
            pv.exception(e)

        elements = ctx.get_serialized_elements()
        assert len(elements) == 1
        el = elements[0]
        assert el["type"] == "exception"
        assert el["props"]["error_type"] == "ZeroDivisionError"
        assert "division by zero in calculation" in el["props"]["message"]
        assert "Traceback" in el["props"]["traceback"]
    finally:
        reset_current_context(token)
