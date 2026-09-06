"""Comprehensive tests for PyView tabular data elements and data editor."""

from pathlib import Path
import tempfile
import pytest
import pandas as pd

import pyview as pv
from pyview.data_utils import normalize_tabular_data, reconstruct_tabular_data
from pyview.column_config import NumberColumn, ProgressColumn, LinkColumn, CheckboxColumn, SelectboxColumn
from pyview.runtime import ScriptRunner, Session, execute_session_run




def test_data_normalization_formats():
    """Verify normalize_tabular_data handles pandas, list[dict], dict[list], and 2D arrays."""
    # 1. Pandas DataFrame
    df = pd.DataFrame({"A": [1, 2], "B": [10.5, 20.5], "C": [True, False], "D": ["x", "y"]})
    norm_df = normalize_tabular_data(df)
    assert norm_df["columns"] == ["A", "B", "C", "D"]
    assert len(norm_df["data"]) == 2
    assert norm_df["data"][0] == [1, 10.5, True, "x"]
    assert norm_df["column_types"]["A"] == "number"
    assert norm_df["column_types"]["C"] == "checkbox"

    # 2. List of Dicts
    records = [{"Name": "Alice", "Age": 30}, {"Name": "Bob", "Age": 25}]
    norm_rec = normalize_tabular_data(records)
    assert norm_rec["columns"] == ["Name", "Age"]
    assert norm_rec["data"] == [["Alice", 30], ["Bob", 25]]
    assert norm_rec["column_types"]["Age"] == "number"

    # 3. Dict of Lists
    dict_lists = {"Item": ["Pen", "Notebook"], "Cost": [2.5, 5.0]}
    norm_dl = normalize_tabular_data(dict_lists)
    assert norm_dl["columns"] == ["Item", "Cost"]
    assert norm_dl["data"] == [["Pen", 2.5], ["Notebook", 5.0]]

    # 4. 2D List of Lists
    grid = [[1, "One"], [2, "Two"]]
    norm_grid = normalize_tabular_data(grid)
    assert norm_grid["columns"] == ["Col 1", "Col 2"]
    assert norm_grid["data"] == [[1, "One"], [2, "Two"]]


def test_data_reconstruction():
    """Verify reconstruct_tabular_data preserves native types upon client edits."""
    # 1. Pandas reconstruction
    df_orig = pd.DataFrame({"Name": ["Alice", "Bob"], "Score": [90, 85]})
    payload = {
        "columns": ["Name", "Score"],
        "data": [["Alice", 95], ["Bob", 88], ["Charlie", 92]],
        "index": [0, 1, 2],
    }
    df_reconstructed = reconstruct_tabular_data(payload, df_orig)
    assert isinstance(df_reconstructed, pd.DataFrame)
    assert len(df_reconstructed) == 3
    assert df_reconstructed.iloc[0]["Score"] == 95

    # 2. List of dicts reconstruction
    list_orig = [{"Name": "Alice", "Score": 90}]
    list_reconstructed = reconstruct_tabular_data(payload, list_orig)
    assert isinstance(list_reconstructed, list)
    assert len(list_reconstructed) == 3
    assert list_reconstructed[2]["Name"] == "Charlie"


@pytest.mark.asyncio
async def test_table_widget_element_generation():
    """Test pv.table() registers a table element with normalized columns and rows."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("pv.table({'City': ['Paris', 'Tokyo'], 'Pop': ['2.1M', '14.0M']}, key='city_table')\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="table_sess")
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        assert len(elements) == 1
        tbl = elements[0]
        assert tbl["type"] == "table"
        assert tbl["id"] == "user_city_table"
        assert tbl["props"]["columns"] == ["City", "Pop"]
        assert len(tbl["props"]["data"]) == 2
    finally:
        if temp_path.exists():
            temp_path.unlink()


@pytest.mark.asyncio
async def test_dataframe_widget_with_column_config():
    """Test pv.dataframe() with column configurations (ProgressColumn, NumberColumn)."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("data = [{'Item': 'Widget A', 'Price': 24.5, 'Stock': 80}]\n")
        f.write("pv.dataframe(\n")
        f.write("    data,\n")
        f.write("    column_config={\n")
        f.write("        'Price': pv.column_config.NumberColumn('Unit Price', format='$%.2f'),\n")
        f.write("        'Stock': pv.column_config.ProgressColumn('Capacity %', min_value=0, max_value=100),\n")
        f.write("    },\n")
        f.write("    key='my_df',\n")
        f.write(")\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="df_sess")
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        df_el = elements[0]
        assert df_el["type"] == "dataframe"
        cfg = df_el["props"]["column_config"]
        assert cfg["Price"]["type"] == "number"
        assert cfg["Price"]["format"] == "$%.2f"
        assert cfg["Stock"]["type"] == "progress"
    finally:
        if temp_path.exists():
            temp_path.unlink()


@pytest.mark.asyncio
async def test_data_editor_two_way_sync():
    """Test pv.data_editor() receives edited payload from client and returns updated data."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("initial = [{'Task': 'Design', 'Done': False}]\n")
        f.write("edited = pv.data_editor(initial, num_rows='dynamic', key='tasks_editor')\n")
        f.write("pv.write('Count:', len(edited))\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="editor_sess")

        # 1. Initial run -> length 1
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        assert session.session_state.tasks_editor == [{'Task': 'Design', 'Done': False}]

        # 2. Client adds a row and commits
        updated_payload = {
            "columns": ["Task", "Done"],
            "data": [["Design", True], ["Build", False]],
            "index": [0, 1],
        }
        gen, elements, error = await execute_session_run(
            session,
            runner,
            pending_values={"user_tasks_editor": updated_payload},
        )
        assert error is None
        assert len(session.session_state.tasks_editor) == 2
        assert session.session_state.tasks_editor[0]["Done"] is True
        write_el = elements[1]
        assert "Count: 2" in write_el["props"]["content"]
    finally:
        if temp_path.exists():
            temp_path.unlink()


@pytest.mark.asyncio
async def test_json_viewer_widget():
    """Test pv.json() registers a collapsible json_viewer element."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import pyview as pv\n")
        f.write("pv.json({'status': 'ok', 'services': ['auth', 'billing']}, expanded=True, key='telemetry')\n")
        temp_path = Path(f.name)

    try:
        runner = ScriptRunner(temp_path)
        session = Session(session_id="json_sess")
        gen, elements, error = await execute_session_run(session, runner)
        assert error is None
        json_el = elements[0]
        assert json_el["type"] == "json_viewer"
        assert json_el["props"]["expanded"] is True
        assert '"status": "ok"' in json_el["props"]["raw_json"]
    finally:
        if temp_path.exists():
            temp_path.unlink()


@pytest.mark.asyncio
async def test_data_showcase_example_executes():
    """Verify examples/data_showcase.py runs cleanly."""
    script_path = Path(__file__).parent.parent / "examples" / "data_showcase.py"
    assert script_path.exists()
    
    runner = ScriptRunner(script_path)
    session = Session(session_id="test_data_showcase")
    
    gen, elements, error = await execute_session_run(session, runner)
    assert error is None, f"Error in data_showcase: {error}"
    assert gen == 1
    assert len(elements) > 0


def test_large_dataframe_vectorized_normalization():
    import pandas as pd
    import numpy as np
    import time
    from pyview.components.data.data_utils import normalize_tabular_data, reconstruct_tabular_data

    n_rows = 10_000
    df = pd.DataFrame({
        "id": range(n_rows),
        "name": [f"Item {i}" for i in range(n_rows)],
        "val": np.random.randn(n_rows),
        "missing": [None if i % 5 == 0 else float(i) for i in range(n_rows)],
    })

    t0 = time.perf_counter()
    norm = normalize_tabular_data(df)
    elapsed = time.perf_counter() - t0

    assert len(norm["columns"]) == 4
    assert len(norm["data"]) == n_rows
    assert elapsed < 0.5
    assert norm["data"][0][3] is None

    recon_df = reconstruct_tabular_data(norm, df)
    assert isinstance(recon_df, pd.DataFrame)
    assert len(recon_df) == n_rows
