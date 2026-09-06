"""PyView Living Documentation — Interactive Documentation Application.

Run with:
    uv run pyview run examples/documentation_showcase.py --port 8501
"""

import time
import pyview as pv

# Configure page settings
pv.set_page_config(
    page_title="PyView Documentation & Interactive Explorer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar Navigation
with pv.sidebar:
    pv.title("📚 PyView Docs")
    pv.write("Pure-Python reactive web framework documentation.")
    
    topic = pv.radio(
        "Navigation",
        [
            "🏠 Overview & Mental Model",
            "📐 Layouts & Containers",
            "🎛️ Form & Input Controls",
            "📊 Data & Data Editor",
            "⚡ Status, Metrics & Toasts",
            "🧠 Caching & Execution Flow",
        ],
        index=0,
    )
    
    pv.divider()
    pv.write("💡 **Quick tip**: Switch sections to test live PyView widgets alongside their code.")


if topic == "🏠 Overview & Mental Model":
    pv.title("🚀 Welcome to PyView")
    pv.write(
        "**PyView** is a lightweight, pure-Python reactive web framework built from scratch with zero Streamlit dependencies. "
        "It executes your Python script top-to-bottom on every user interaction, streaming lightweight JSON element trees over WebSockets."
    )
    
    col1, col2, col3 = pv.columns(3)
    with col1:
        pv.metric("Rerun Latency", "< 5ms", "Sub-millisecond diff")
    with col2:
        pv.metric("Build Dependencies", "0", "Zero Node/Webpack", delta_color="inverse")
    with col3:
        pv.metric("API Exports", "80+", "Full UI Toolkit")
        
    pv.header("Interactive Counter Demo")
    pv.write("Every button click or widget adjustment simply re-executes this script from the top:")
    
    if "doc_counter" not in pv.session_state:
        pv.session_state["doc_counter"] = 10
        
    c1, c2, c3 = pv.columns([1, 1, 2])
    with c1:
        if pv.button("➕ Increment (+1)", key="btn_inc_doc"):
            pv.session_state["doc_counter"] += 1
    with c2:
        if pv.button("🔄 Reset Counter", key="btn_reset_doc"):
            pv.session_state["doc_counter"] = 0
    with c3:
        pv.metric("Current Value", pv.session_state["doc_counter"])


elif topic == "📐 Layouts & Containers":
    pv.title("📐 Layouts & Containers")
    pv.write("Organize your user interface using Python's `with` statement:")
    
    t1, t2, t3 = pv.tabs(["Multi-Column Grid", "Cards & Accordions", "Forms"])
    
    with t1:
        pv.header("pv.columns([weights...])")
        pv.write("Split elements across proportional or equal column widths:")
        left, right = pv.columns([2, 1])
        with left:
            with pv.card():
                pv.write("### Main Content Column (Weight 2)")
                pv.write("Ideal for primary data tables, charts, or detailed forms.")
        with right:
            with pv.card():
                pv.write("### Aside (Weight 1)")
                pv.metric("Active Sessions", 142, "+12%")
                
    with t2:
        pv.header("pv.expander & pv.card")
        with pv.expander("Click to reveal advanced parameters"):
            pv.write("Expanders keep secondary details cleanly tucked away without cluttering the screen.")
            pv.slider("Threshold Sensitivity", 0, 100, 50)
            
    with t3:
        pv.header("pv.form & Batched Submissions")
        pv.write("Forms batch input values until the submit button is triggered:")
        with pv.form("user_survey_form"):
            username = pv.text_input("Name", value="Jane Doe")
            role = pv.selectbox("Primary Role", ["Engineer", "Data Scientist", "Designer", "Product"])
            submitted = pv.form_submit_button("Submit Survey")
            if submitted:
                pv.success(f"Form received! Thank you, {username} ({role}).")


elif topic == "🎛️ Form & Input Controls":
    pv.title("🎛️ Form & Input Controls")
    pv.write("PyView includes 16+ rich interactive inputs:")
    
    col_a, col_b = pv.columns(2)
    with col_a:
        pv.header("Text & Selection")
        txt = pv.text_input("Project Name", value="Nova AI Engine")
        category = pv.segmented_control("Deployment Tier", ["Dev", "Staging", "Production"], default="Dev")
        tags = pv.pills("Features", ["FastAPI", "WebSockets", "Reactive", "Pandas"], default=["FastAPI"])
        is_active = pv.toggle("Live Telemetry", value=True)
        
    with col_b:
        pv.header("Numeric & Sliders")
        val = pv.slider("Concurrency Workers", min_value=1, max_value=32, value=8)
        num = pv.number_input("Port Number", min_value=1024, max_value=65535, value=8501)
        rating = pv.feedback("stars")
        
    pv.divider()
    pv.write("### Live Widget State:")
    pv.json({
        "project": txt,
        "tier": category,
        "tags": tags,
        "active": is_active,
        "workers": val,
        "port": num,
        "feedback_rating": rating,
    })


elif topic == "📊 Data & Data Editor":
    pv.title("📊 Tabular Data & Editable Grids")
    pv.write("Render rich interactive dataframes or allow inline cell editing:")
    
    sample_records = [
        {"Task": "Fix WebSocket reconnect", "Owner": "Alex", "Done": True, "Priority": 1},
        {"Task": "Add LinkColumn support", "Owner": "Sam", "Done": False, "Priority": 2},
        {"Task": "Documentation release", "Owner": "Jordan", "Done": True, "Priority": 1},
    ]
    
    t_df, t_editor = pv.tabs(["Interactive DataFrame", "Reactive Data Editor"])
    
    with t_df:
        pv.dataframe(sample_records, use_container_width=True)
        
    with t_editor:
        pv.write("Edit cells, toggle checkboxes, or add rows:")
        edited = pv.data_editor(sample_records, num_rows="dynamic", key="sample_editor")
        pv.write("### Current Grid State:")
        pv.json(edited)


elif topic == "⚡ Status, Metrics & Toasts":
    pv.title("⚡ Status & Feedback Indicators")
    pv.write("Trigger notifications and status alerts dynamically:")
    
    c1, c2 = pv.columns(2)
    with c1:
        pv.success("Operation completed successfully!")
        pv.info("Note: Worker threads are running in the background.")
        pv.warning("High memory usage detected.")
        pv.error("Failed to connect to secondary database.")
        
    with c2:
        if pv.button("🎈 Trigger Balloons"):
            pv.balloons()
            pv.toast("Celebration triggered!", icon="🎉")
            
        if pv.button("❄️ Trigger Snow"):
            pv.snow()
            pv.toast("Winter snowfall!", icon="❄️")
            
        if pv.button("🍞 Show Simple Toast"):
            pv.toast("Real-time notification received", icon="🔔")


elif topic == "🧠 Caching & Execution Flow":
    pv.title("🧠 Caching & Performance Primitives")
    pv.write("Optimize performance with built-in caching decorators:")
    
    @pv.cache_data(ttl=30)
    def compute_heavy_dataset(size: int):
        time.sleep(0.5)  # Simulate expensive work
        return [f"Item {i} (computed at {time.strftime('%H:%M:%S')})" for i in range(size)]
        
    count = pv.slider("Data Size", 3, 10, 5)
    
    if pv.button("Compute Data (Cached for 30s)"):
        with pv.spinner("Computing dataset..."):
            result = compute_heavy_dataset(count)
        pv.success(f"Loaded {len(result)} items!")
        pv.write(result)
        
    if pv.button("🧹 Clear Function Cache"):
        compute_heavy_dataset.clear()
        pv.toast("Cache cleared!", icon="🧹")
