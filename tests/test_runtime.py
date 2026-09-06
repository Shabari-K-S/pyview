"""Comprehensive test suite for PyView runtime, state, widgets, concurrency, and server."""

import asyncio
from pathlib import Path
import tempfile
import pytest
from starlette.testclient import TestClient

import pyview as pv
from pyview.context import ExecutionContext, get_current_context, set_current_context, reset_current_context
from pyview.runtime import ScriptRunner, Session, SessionManager, execute_session_run
from pyview.server import create_app
from pyview.state import SessionState


def test_session_state_dict_and_attr_access():
    """Test SessionState behaves as both dictionary and attribute container."""
    state = SessionState()
    state.count = 42
    assert state["count"] == 42
    assert "count" in state
    assert state.get("count") == 42
    assert state.setdefault("name", "PyView") == "PyView"
    assert state.name == "PyView"

    # Test deletion
    del state.count
    assert "count" not in state
    with pytest.raises(AttributeError):
        _ = state.count


def test_context_protection():
    """Test accessing widgets or session_state outside execution context raises RuntimeError."""
    with pytest.raises(RuntimeError, match="outside of an active script execution context"):
        _ = pv.session_state.count

    with pytest.raises(RuntimeError, match="outside of an active script execution context"):
        pv.button("Test Button")


def test_widget_id_derivation():
    """Test widget key resolution and positional counter fallbacks."""
    session = Session(session_id="test_sess")
    ctx = ExecutionContext(session=session, generation=1)

    # Positional counter
    id1 = ctx.get_widget_id("button", None)
    id2 = ctx.get_widget_id("button", None)
    id3 = ctx.get_widget_id("text_input", None)
    assert id1 == "button_1"
    assert id2 == "button_2"
    assert id3 == "text_input_1"

    # Custom user key
    id_custom = ctx.get_widget_id("button", "my_custom_btn")
    assert id_custom == "user_my_custom_btn"


@pytest.mark.asyncio
async def test_counter_app_execution_and_transient_trigger():
    """Test running counter.py: initial run, button click trigger, and subsequent reset."""
    counter_script = Path(__file__).parent.parent / "examples" / "counter.py"
    runner = ScriptRunner(counter_script)
    session = Session(session_id="sess_1")

    # 1. Initial run
    gen, elements, error = await execute_session_run(session, runner)
    assert error is None
    assert gen == 1
    assert len(elements) > 0
    assert session.session_state.count == 0
    assert int(session.session_state.step_size) == 1

    # 2. Click increment button
    gen, elements, error = await execute_session_run(
        session,
        runner,
        active_triggers={"user_btn_inc"},
    )
    assert error is None
    assert gen == 2
    assert session.session_state.count == 1
    assert any("Added 1" in h for h in session.session_state.history)

    # 3. Subsequent rerun without triggers -> button resets to False, count stays 1

    gen, elements, error = await execute_session_run(session, runner)
    assert error is None
    assert gen == 3
    assert session.session_state.count == 1

    # 4. Change step size to 5 and click increment
    gen, elements, error = await execute_session_run(
        session,
        runner,
        active_triggers={"user_btn_inc"},
        pending_values={"user_step_size": 5},
    )
    assert error is None
    assert session.session_state.count == 6
    assert int(session.session_state.step_size) == 5

    # 5. Click reset button
    gen, elements, error = await execute_session_run(
        session,
        runner,
        active_triggers={"user_btn_reset"},
    )
    assert error is None
    assert session.session_state.count == 0


@pytest.mark.asyncio
async def test_session_concurrency_isolation():
    """Test two sessions run independently without state cross-contamination."""
    counter_script = Path(__file__).parent.parent / "examples" / "counter.py"
    runner = ScriptRunner(counter_script)

    sess_a = Session(session_id="sess_a")
    sess_b = Session(session_id="sess_b")

    # Increment Session A 3 times
    for _ in range(3):
        await execute_session_run(sess_a, runner, active_triggers={"user_btn_inc"})

    # Increment Session B 1 time with step=10
    await execute_session_run(
        sess_b,
        runner,
        active_triggers={"user_btn_inc"},
        pending_values={"user_step_size": 10},
    )

    assert sess_a.session_state.count == 3
    assert sess_b.session_state.count == 10



@pytest.mark.asyncio
async def test_clean_exception_handling():
    """Test script exception is caught cleanly and formatted without crashing."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("pv.title('Error Demo')\n")
        f.write("raise ZeroDivisionError('Deliberate test error')\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="error_sess")

        gen, elements, error = await execute_session_run(session, runner)
        assert error is not None
        assert "ZeroDivisionError: Deliberate test error" in error
        # Verify title was rendered before error was raised
        assert len(elements) == 1
        assert elements[0]["type"] == "title"
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_fastapi_server_and_websocket():
    """Test FastAPI application, static serving, and WebSocket transport."""
    counter_script = Path(__file__).parent.parent / "examples" / "counter.py"
    app = create_app(counter_script)
    client = TestClient(app)

    # Test HTTP GET /
    response = client.get("/")
    assert response.status_code == 200
    assert "PyView" in response.text

    # Test WebSocket connection & interactive loop
    with client.websocket_connect("/_pyview/ws") as ws:
        # 1. Receive connected handshake
        msg_conn = ws.receive_json()
        assert msg_conn["type"] == "connected"
        assert "session_id" in msg_conn

        # 2. Receive running status
        msg_status = ws.receive_json()
        assert msg_status["type"] == "status"
        assert msg_status["status"] == "running"

        # 3. Receive initial render
        msg_render = ws.receive_json()
        assert msg_render["type"] == "render"
        assert len(msg_render["elements"]) > 0

        # 4. Receive idle status
        msg_idle = ws.receive_json()
        assert msg_idle["type"] == "status"
        assert msg_idle["status"] == "idle"

        # 5. Send button click event
        ws.send_json({
            "type": "event",
            "id": "user_btn_inc",
            "value": True,
            "widget_type": "button",
        })

        # Receive running status
        msg_status2 = ws.receive_json()
        assert msg_status2["type"] == "status"
        assert msg_status2["status"] == "running"

        # Receive updated render
        msg_render2 = ws.receive_json()
        assert msg_render2["type"] == "render"
        # Verify count updated to 1
        header_el = next((e for e in msg_render2["elements"] if e["type"] == "header"), None)
        assert header_el is not None
        assert "Current Count: 1" in header_el["props"]["text"]

        # Receive idle status
        msg_idle2 = ws.receive_json()
        assert msg_idle2["type"] == "status"
        assert msg_idle2["status"] == "idle"


@pytest.mark.asyncio
async def test_positional_widgets_without_keys():
    """Test multiple widgets without explicit keys are given unique positional IDs."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("pv.title('Positional')\n")
        f.write("b1 = pv.button('Btn 1')\n")
        f.write("b2 = pv.button('Btn 2')\n")
        f.write("t1 = pv.text_input('Input 1', value='val1')\n")
        f.write("t2 = pv.text_input('Input 2', value='val2')\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="pos_sess")
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        ids = [e["id"] for e in elements]
        assert "title_1" in ids
        assert "button_1" in ids
        assert "button_2" in ids
        assert "text_input_1" in ids
        assert "text_input_2" in ids

        # Trigger button_2 specifically
        gen, elements, error = await execute_session_run(
            session, runner, active_triggers={"button_2"}
        )
        assert error is None
        assert gen == 2
    finally:
        if temp_path.exists():
            temp_path.unlink()


@pytest.mark.asyncio
async def test_write_formatting():
    """Test write handles dicts, lists, numbers, strings, and custom objects."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("pv.write('Simple text')\n")
        f.write("pv.write({'key': 'value', 'num': 123})\n")
        f.write("pv.write(['item1', 'item2'])\n")
        f.write("pv.write('Part 1', 'Part 2', 42)\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="write_sess")
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        assert len(elements) == 4
        assert elements[0]["props"]["content_type"] == "text"
        assert elements[0]["props"]["content"] == "Simple text"
        assert elements[1]["props"]["content_type"] == "json"
        assert '"key": "value"' in elements[1]["props"]["content"]
        assert elements[2]["props"]["content_type"] == "json"
        assert elements[3]["props"]["content"] == "Part 1 Part 2 42"
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_cli_version_and_help(capsys):
    """Test CLI runs without crashing for help and version."""
    import sys
    from pyview.cli import main

    # Test --version
    with pytest.raises(SystemExit) as exc:
        sys.argv = ["pyview", "--version"]
        main()
    assert exc.value.code == 0

    # Test help
    with pytest.raises(SystemExit) as exc:
        sys.argv = ["pyview", "-h"]
        main()
    assert exc.value.code == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "example_name",
    [
        "counter.py",
        "todo_app.py",
        "form_validation.py",
        "converter.py",
        "quiz_app.py",
        "dashboard.py",
        "layout_showcase.py",
        "data_showcase.py",
        "inputs_showcase.py",
        "status_showcase.py",
        "media_showcase.py",
        "flow_showcase.py",
        "documentation_showcase.py",
    ],
)
async def test_all_examples_execute_cleanly(example_name: str):
    """Verify that all packaged examples compile and execute initial run without errors."""
    script_path = Path(__file__).parent.parent / "examples" / example_name
    assert script_path.exists(), f"Example script not found: {example_name}"
    
    runner = ScriptRunner(script_path)
    session = Session(session_id=f"test_{example_name}")
    
    gen, elements, error = await execute_session_run(session, runner)
    assert error is None, f"Error in {example_name}: {error}"
    assert gen == 1
    assert len(elements) > 0


@pytest.mark.asyncio
async def test_columns_and_container_scoped_keys():
    """Test multi-column nesting and container-scoped positional fallback widget IDs."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("col1, col2 = pv.columns([2, 1])\n")
        f.write("with col1:\n")
        f.write("    pv.button('Col1 Btn')\n")
        f.write("with col2:\n")
        f.write("    pv.button('Col2 Btn')\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="col_sess")
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        assert len(elements) == 1
        cols_el = elements[0]
        assert cols_el["type"] == "columns"
        assert len(cols_el["children"]) == 2

        # Check column 1 children and scoped widget id
        c1 = cols_el["children"][0]
        assert c1["props"]["weight"] == 2
        assert len(c1["children"]) == 1
        assert c1["children"][0]["id"] == "columns_1.col_0.button_1"

        # Check column 2 children and scoped widget id
        c2 = cols_el["children"][1]
        assert c2["props"]["weight"] == 1
        assert len(c2["children"]) == 1
        assert c2["children"][0]["id"] == "columns_1.col_1.button_1"
    finally:
        if temp_path.exists():
            temp_path.unlink()


@pytest.mark.asyncio
async def test_tabs_container_full_execution():
    """Test all tab branches are fully computed top-to-bottom on every rerun."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("t1, t2 = pv.tabs(['Overview', 'Settings'])\n")
        f.write("with t1:\n")
        f.write("    pv.write('Overview Content')\n")
        f.write("with t2:\n")
        f.write("    pv.write('Settings Content')\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="tab_sess")
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        assert len(elements) == 1
        tabs_el = elements[0]
        assert tabs_el["type"] == "tabs"
        assert len(tabs_el["children"]) == 2

        tab1 = tabs_el["children"][0]
        assert tab1["props"]["label"] == "Overview"
        assert tab1["children"][0]["props"]["content"] == "Overview Content"

        tab2 = tabs_el["children"][1]
        assert tab2["props"]["label"] == "Settings"
        assert tab2["children"][0]["props"]["content"] == "Settings Content"
    finally:
        if temp_path.exists():
            temp_path.unlink()


@pytest.mark.asyncio
async def test_expander_persisted_toggle_state():
    """Test expander open/closed state persists across reruns via session_state."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("with pv.expander('Advanced Options', expanded=False, key='my_exp'):\n")
        f.write("    pv.write('Inner details')\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="exp_sess")

        # 1. Initial run -> default expanded=False
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        exp_el = elements[0]
        assert exp_el["props"]["expanded"] is False

        # 2. Client toggles expander open (sends True)
        gen, elements, error = await execute_session_run(
            session, runner, pending_values={"user_my_exp": True}
        )
        assert error is None
        assert session.session_state.my_exp is True
        assert elements[0]["props"]["expanded"] is True

        # 3. Subsequent rerun without event -> state remains open (True)
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        assert elements[0]["props"]["expanded"] is True
    finally:
        if temp_path.exists():
            temp_path.unlink()


@pytest.mark.asyncio
async def test_sidebar_container():
    """Test with pv.sidebar: routes elements into the dedicated sidebar container."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("with pv.sidebar:\n")
        f.write("    pv.title('Sidebar Title')\n")
        f.write("pv.title('Main Title')\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="sb_sess")
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        assert len(elements) == 2

        # First element is sidebar container
        sb_el = elements[0]
        assert sb_el["type"] == "sidebar"
        assert len(sb_el["children"]) == 1
        assert sb_el["children"][0]["props"]["text"] == "Sidebar Title"

        # Second element is main canvas element
        main_el = elements[1]
        assert main_el["type"] == "title"
        assert main_el["props"]["text"] == "Main Title"
    finally:
        if temp_path.exists():
            temp_path.unlink()



@pytest.mark.asyncio
async def test_selectbox_server_side_index_resolution():
    """Test selectbox resolves options[index] on the backend when client sends integer index."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("res = pv.selectbox('Pick Fruit', options=['Apple', 'Banana', 'Cherry'], index=0, key='fruit')\n")
        f.write("pv.write('Selected:', res)\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="select_sess")

        # 1. Initial run -> default index 0 = 'Apple'
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        assert session.session_state.fruit == "Apple"
        select_el = next(e for e in elements if e["type"] == "selectbox")
        assert select_el["props"]["selected_index"] == 0

        # 2. Client sends selected index 2 (Cherry)
        gen, elements, error = await execute_session_run(
            session,
            runner,
            pending_values={"user_fruit": 2},
        )
        assert error is None
        assert session.session_state.fruit == "Cherry"
        write_el = next(e for e in elements if e["type"] == "write")
        assert "Selected: Cherry" in write_el["props"]["content"]
    finally:
        if temp_path.exists():
            temp_path.unlink()


@pytest.mark.asyncio
async def test_widget_input_validations():
    """Test ValueError raised during execution for invalid widget parameters."""
    # 1. Empty selectbox options
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("pv.selectbox('Empty', options=[])\n")
        p1 = Path(f.name)

    # 2. Slider min > max
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("pv.slider('Invalid Slider', min_value=100, max_value=10)\n")
        p2 = Path(f.name)

    # 3. Number input min > max
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("pv.number_input('Invalid Num', min_value=50, max_value=20)\n")
        p3 = Path(f.name)

    # 4. Metric invalid delta_color
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("pv.metric('Label', '100', delta='+5', delta_color='invalid_mode')\n")
        p4 = Path(f.name)

    try:
        session = Session(session_id="val_sess")
        
        _, _, err1 = await execute_session_run(session, ScriptRunner(p1))
        assert err1 is not None and "selectbox options cannot be empty" in err1

        _, _, err2 = await execute_session_run(session, ScriptRunner(p2))
        assert err2 is not None and "min_value (100) cannot be greater than max_value (10)" in err2

        _, _, err3 = await execute_session_run(session, ScriptRunner(p3))
        assert err3 is not None and "min_value (50) cannot be greater than max_value (20)" in err3

        _, _, err4 = await execute_session_run(session, ScriptRunner(p4))
        assert err4 is not None and "metric delta_color must be one of" in err4
    finally:
        for p in (p1, p2, p3, p4):
            if p.exists():
                p.unlink()


@pytest.mark.asyncio
async def test_metric_delta_semantics_and_alerts():
    """Test metric delta color modes and status alert element generation."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("pv.metric('Rev', '$100', delta='+10%', delta_color='normal')\n")
        f.write("pv.metric('Cost', '$50', delta='+5%', delta_color='inverse')\n")
        f.write("pv.metric('Latency', '10ms', delta='0%', delta_color='off')\n")
        f.write("pv.success('All good', key='succ_1')\n")
        f.write("pv.info('Note this', key='info_1')\n")
        f.write("pv.warning('Watch out', key='warn_1')\n")
        f.write("pv.error('Failed', key='err_1')\n")
        f.write("pv.divider(key='div_1')\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="metric_sess")
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        assert len(elements) == 8

        # Verify metric properties
        m_rev = elements[0]
        assert m_rev["type"] == "metric"
        assert m_rev["props"]["delta_color"] == "normal"
        assert m_rev["props"]["delta_direction"] == "positive"

        m_cost = elements[1]
        assert m_cost["props"]["delta_color"] == "inverse"
        assert m_cost["props"]["delta_direction"] == "positive"

        m_lat = elements[2]
        assert m_lat["props"]["delta_color"] == "off"

        # Verify alerts and divider
        assert elements[3]["type"] == "alert" and elements[3]["props"]["alert_type"] == "success"
        assert elements[4]["type"] == "alert" and elements[4]["props"]["alert_type"] == "info"
        assert elements[5]["type"] == "alert" and elements[5]["props"]["alert_type"] == "warning"
        assert elements[6]["type"] == "alert" and elements[6]["props"]["alert_type"] == "error"
        assert elements[7]["type"] == "divider"
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_stale_session_cleanup():
    import time
    from pyview.core.runtime import SessionManager

    mgr = SessionManager()
    s1 = mgr.get_or_create("active_session")
    s2 = mgr.get_or_create("disconnected_session")
    s2.disconnected_at = time.time() - 4000
    s3 = mgr.get_or_create("idle_session")
    s3.last_active_at = time.time() - 90000

    assert len(mgr.list_sessions()) == 3
    mgr.cleanup_stale_sessions(max_idle_seconds=3600.0)
    remaining = mgr.list_sessions()
    assert len(remaining) == 1
    assert remaining[0].session_id == "active_session"


def test_session_state_iteration_and_keys():
    session = Session(session_id="iter_sess")
    session.session_state.a = 1
    session.session_state.b = "two"
    session.session_state["c"] = [3]

    keys = list(session.session_state)
    assert set(keys) == {"a", "b", "c"}
    assert [session.session_state[k] for k in session.session_state] == [1, "two", [3]]

