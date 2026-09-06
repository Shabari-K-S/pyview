"""Unit tests for Execution Flow & Application Logic (stop, rerun, cache_data, cache_resource, set_page_config, query_params)."""

import asyncio
from pathlib import Path
import tempfile
import time
import pytest
from pyview.core.cache import cache_data, cache_resource
from pyview.core.context import ExecutionContext, reset_current_context, set_current_context
from pyview.core.flow import RerunException, StopException
from pyview.core.runtime import ScriptRunner, Session, execute_session_run
import pyview as pv


@pytest.fixture
def session():
    return Session(session_id="test_flow_session")


def test_cache_data_memoization_and_clear():
    call_count = 0

    @cache_data
    def compute_heavy_sum(a: int, b: int) -> int:
        nonlocal call_count
        call_count += 1
        return a + b

    # Initial call
    res1 = compute_heavy_sum(10, 20)
    assert res1 == 30
    assert call_count == 1

    # Cached call
    res2 = compute_heavy_sum(10, 20)
    assert res2 == 30
    assert call_count == 1  # Not incremented

    # Different arguments
    res3 = compute_heavy_sum(5, 5)
    assert res3 == 10
    assert call_count == 2

    # Clear cache
    compute_heavy_sum.clear()
    res4 = compute_heavy_sum(10, 20)
    assert res4 == 30
    assert call_count == 3


def test_cache_data_ttl_expiration():
    counter = 0

    @cache_data(ttl=0.1)
    def get_timestamp_data():
        nonlocal counter
        counter += 1
        return counter

    assert get_timestamp_data() == 1
    assert get_timestamp_data() == 1

    time.sleep(0.15)
    # Cache should have expired
    assert get_timestamp_data() == 2


def test_cache_resource_singleton():
    created = 0

    class DBConnection:
        def __init__(self):
            nonlocal created
            created += 1

    @cache_resource
    def get_connection():
        return DBConnection()

    c1 = get_connection()
    c2 = get_connection()
    assert c1 is c2
    assert created == 1

    get_connection.clear()
    c3 = get_connection()
    assert c3 is not c1
    assert created == 2


def test_page_config_validation_and_registration(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        pv.set_page_config(
            page_title="My Analytics App",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        assert ctx.page_config is not None
        assert ctx.page_config.page_title == "My Analytics App"
        assert ctx.page_config.page_icon == "📊"
        assert ctx.page_config.layout == "wide"
        assert ctx.page_config.initial_sidebar_state == "expanded"

        # Invalid layout raises ValueError
        with pytest.raises(ValueError, match="layout must be 'centered' or 'wide'"):
            pv.set_page_config(layout="invalid_layout")  # type: ignore

        # Invalid sidebar state raises ValueError
        with pytest.raises(ValueError, match="initial_sidebar_state must be"):
            pv.set_page_config(initial_sidebar_state="invalid_state")  # type: ignore
    finally:
        reset_current_context(token)


def test_query_params_proxy_operations(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        session.query_params = {"view": "dashboard", "page": "1"}

        # Read
        assert pv.query_params["view"] == "dashboard"
        assert pv.query_params.get("page") == "1"
        assert "view" in pv.query_params
        assert "missing" not in pv.query_params

        # Write & Mutation tracking
        assert ctx.query_params_mutated is False
        pv.query_params["filter"] = "active"
        assert ctx.query_params_mutated is True
        assert session.query_params["filter"] == "active"

        # Update
        pv.query_params.update({"item": "123"})
        assert session.query_params["item"] == "123"

        # Delete
        del pv.query_params["page"]
        assert "page" not in session.query_params

        # to_dict
        d = pv.query_params.to_dict()
        assert d == {"view": "dashboard", "filter": "active", "item": "123"}
    finally:
        reset_current_context(token)


@pytest.mark.asyncio
async def test_stop_execution_graceful_exit():
    """Verify that pv.stop() stops execution immediately and preserves prior elements without errors."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("pv.title('Rendered Step 1')\n")
        f.write("pv.stop()\n")
        f.write("pv.title('Should NEVER render Step 2')\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="test_stop_sess")

        res = await execute_session_run(session, runner)
        gen, elements, error = res
        assert error is None
        assert len(elements) == 1
        assert elements[0]["type"] == "title"
        assert elements[0]["props"]["text"] == "Rendered Step 1"
    finally:
        if temp_path.exists():
            temp_path.unlink()


@pytest.mark.asyncio
async def test_rerun_execution_flow():
    """Verify that pv.rerun() triggers an immediate rerun iteration."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("if 'counter' not in pv.session_state:\n")
        f.write("    pv.session_state.counter = 0\n")
        f.write("if pv.session_state.counter == 0:\n")
        f.write("    pv.session_state.counter = 1\n")
        f.write("    pv.rerun()\n")
        f.write("pv.title(f'Final Counter: {pv.session_state.counter}')\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="test_rerun_sess")

        res = await execute_session_run(session, runner)
        gen, elements, error = res
        assert error is None
        assert session.session_state.counter == 1
        assert len(elements) == 1
        assert elements[0]["props"]["text"] == "Final Counter: 1"
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_cache_lru_eviction():
    calls = []

    @cache_data(max_entries=2)
    def compute(x: int) -> int:
        calls.append(x)
        return x * 2

    assert compute(1) == 2
    assert compute(2) == 4
    assert calls == [1, 2]

    # Access 1 again -> 1 becomes most recently used
    assert compute(1) == 2
    assert calls == [1, 2]

    # Add 3 -> 2 should be evicted (least recently used)
    assert compute(3) == 6
    assert calls == [1, 2, 3]

    # 1 is still cached
    assert compute(1) == 2
    assert calls == [1, 2, 3]

    # 2 was evicted, so calling compute(2) re-executes
    assert compute(2) == 4
    assert calls == [1, 2, 3, 2]


@pytest.mark.asyncio
async def test_session_cancellation_during_run():
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("pv.title('First')\n")
        f.write("from pyview.core.context import get_current_context\n")
        f.write("get_current_context().session.cancel()\n")
        f.write("pv.title('Second')\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="test_cancel_sess")
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        assert len(elements) == 0
    finally:
        if temp_path.exists():
            temp_path.unlink()

