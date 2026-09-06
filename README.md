# PyView 🚀

A lightweight, pure-Python reactive web framework built from scratch with zero Streamlit dependencies.

## Key Features

- **Top-to-Bottom Rerun**: Scripts execute top-to-bottom on every user interaction.
- **Data & Tables**:
  - `pv.dataframe(df)`: Interactive tables with search, column sorting, pagination, and CSV download.
  - `pv.data_editor(df, num_rows="dynamic")`: Reactive editable grid with inline cell editing, checkbox toggles, select dropdowns, and dynamic row addition/deletion.
  - `pv.column_config`: Column formatters (`NumberColumn`, `TextColumn`, `CheckboxColumn`, `SelectboxColumn`, `ProgressColumn`, `LinkColumn`).
  - `pv.table(df)`: Semantic HTML static tables.
  - `pv.json(data)`: Collapsible JSON tree explorer with copy-to-clipboard.
  - `pv.metric(label, value, delta)`: KPI metric cards with normal, inverse, and off delta coloring.
- **Hierarchical Layout Containers**: Multi-column grids (`pv.columns`), tabbed switchers (`pv.tabs`), collapsible accordions (`pv.expander`), surface cards (`pv.card`), and sidebars (`pv.sidebar`) using Python's `with` statement.
- **Container-Scoped Identity**: Un-keyed widgets inside nested columns/tabs derive container-scoped paths (e.g. `columns_1.col_0.button_1`), preventing positional collision.
- **State & Identity**: `pv.session_state` persists across reruns. Expanders and widgets preserve their open/closed and value states across rerun cycles.
- **Transient vs. Persistent State**:
  - `pv.button(...)` evaluates to `True` strictly during the rerun caused by its click, then resets to `False`.
  - `pv.text_input(...)`, `pv.slider(...)`, `pv.selectbox(...)`, `pv.checkbox(...)`, and `pv.data_editor(...)` persist value changes.
- **Instant Client-Side Tabs**: All tab panes are computed server-side, allowing instant client-side tab switching without WebSocket round-trips.
- **Async Concurrency**: FastAPI + WebSockets transport lightweight JSON element trees. User scripts execute in background worker threads without blocking the async event loop.
- **Vanilla Frontend**: Pure HTML/CSS/JS frontend without node, npm, or build steps.
- **Clean Exception Handling**: Script tracebacks are formatted into the UI without crashing the server.

---

## Quick Start

```bash
# Sync dependencies
uv sync

# Run the data showcase
uv run pyview run examples/data_showcase.py --port 8501
```

Open `http://127.0.0.1:8501` in your browser.

---

## 📚 Documentation & Interactive Explorer

PyView includes a complete documentation portal with dark/light themes, instant search, copyable snippets, and interactive widget demos:

1. **Serve Local Documentation Portal**:
   ```bash
   uv run pyview docs --port 8000
   ```
   *Opens the documentation portal at `http://127.0.0.1:8000` (ready for GitHub Pages or static web servers).*

2. **Interactive Living Documentation App**:
   ```bash
   uv run pyview run examples/documentation_showcase.py --port 8501
   ```
   *Runs a full PyView application that documents PyView using live PyView widgets.*

---

## Included Examples

| Script | Description |
| :--- | :--- |
| [`examples/documentation_showcase.py`](examples/documentation_showcase.py) | **Living Documentation Explorer**: Interactive showcase of all PyView components, layout containers, forms, and caching mechanics. |
| [`examples/data_showcase.py`](examples/data_showcase.py) | **Data Elements Showcase**: Interactive dataframes with sorting/search/progress bars, dynamic live order batch data editor, static shipping table, and collapsible JSON telemetry. |
| [`examples/layout_showcase.py`](examples/layout_showcase.py) | **Layout Containers Showcase**: Sidebar, multi-column metric grids, multi-tab workload forecasting, and diagnostics expanders. |
| [`examples/dashboard.py`](examples/dashboard.py) | **Executive Dashboard**: KPI metrics with normal & inverse deltas, sliders, selectboxes, checkboxes, text areas, and status alerts. |
| [`examples/todo_app.py`](examples/todo_app.py) | Daily task planner with priority badges, status toggles, inline creation card, and productivity statistics. |
| [`examples/counter.py`](examples/counter.py) | Clean digital counter with step sizing, increment/decrement/reset buttons, and action history. |
| [`examples/form_validation.py`](examples/form_validation.py) | Community registration portal with 2-column input card, regex email validation, instant error alerts, and member directory. |
| [`examples/converter.py`](examples/converter.py) | Scientific measurement converter (Temperature, Distance, Weight) with instant formula cards and precision slider. |
| [`examples/quiz_app.py`](examples/quiz_app.py) | Interactive Python & systems trivia quiz with 2x2 answer grid, instant feedback, and deep-dive explanation expanders. |


---

## Running the Examples

```bash
# 1. Full Layout Showcase (Sidebar + Columns + Tabs + Expanders)
uv run pyview run examples/layout_showcase.py --port 8501

# 2. Executive Performance Dashboard
uv run pyview run examples/dashboard.py --port 8501

# 3. Todo Task Manager
uv run pyview run examples/todo_app.py --port 8501

# 4. Form Validation App
uv run pyview run examples/form_validation.py --port 8501

# 5. Universal Unit Converter
uv run pyview run examples/converter.py --port 8501

# 6. Interactive Trivia Quiz
uv run pyview run examples/quiz_app.py --port 8501
```

---

## Running Tests

```bash
uv run pytest -v
```
