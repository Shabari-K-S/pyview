"""AppDynamics — Execution Flow & Performance Hub.

Interactive PyView showcase for Execution Flow & Application Logic:
- Page configuration (wide mode, custom emoji tab icon, and title)
- Memoized data loading with @pv.cache_data & cache invalidation
- Singleton resource management with @pv.cache_resource
- Reactive two-way URL query parameter deep linking
- Graceful execution branching and early exit with pv.stop()
"""

import time
import pyview as pv

# Configure browser page metadata
pv.set_page_config(
    page_title="AppDynamics — Execution Flow & Performance",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global Cached Resource
class MockMLPipeline:
    def __init__(self):
        self.load_time = time.strftime("%H:%M:%S")
        self.model_version = "v3.4.1-neural-distil"

@pv.cache_resource
def get_inference_engine() -> MockMLPipeline:
    return MockMLPipeline()

# Cached Data Function
@pv.cache_data(ttl=60)
def generate_telemetry_records(cluster_id: str, record_count: int = 5) -> list[dict]:
    # Simulate heavy database calculation
    records = []
    for i in range(1, record_count + 1):
        records.append({
            "Node": f"{cluster_id}-node-{i}",
            "CPU_Load": f"{20 + (i * 12) % 75}%",
            "Memory_GB": 16 * i,
            "Latency_ms": 1.2 * i,
            "Status": "Healthy" if i % 4 != 0 else "Degraded",
        })
    return records


# Sidebar Controls
with pv.sidebar:
    pv.title("⚡ System Controls")
    active_cluster = pv.selectbox("Target Compute Cluster", ["us-east-cluster-01", "eu-west-cluster-04", "ap-south-cluster-09"])
    sample_limit = pv.slider("Sample Records", min_value=3, max_value=10, value=5)

    if pv.button("🔄 Clear Data Cache", key="btn_clear_cache"):
        generate_telemetry_records.clear()
        pv.toast("Data cache invalidated! Next load will recompute.", icon="🧹")

    if pv.button("🔄 Force App Rerun", key="btn_force_rerun"):
        pv.rerun()

pv.title("⚡ AppDynamics — Execution Flow & Performance Hub")
pv.write("Explore PyView's execution flow control, deterministic memoization caches, and bidirectional URL deep linking.")

# Query Parameter Deep Linking
current_view = pv.query_params.get("view", "telemetry")
nav_choice = pv.segmented_control("Navigation View", ["telemetry", "pipeline", "auth_gate"], default=current_view)

# Sync choice back to URL query parameters
if nav_choice != pv.query_params.get("view"):
    pv.query_params["view"] = nav_choice

if nav_choice == "auth_gate":
    pv.header("🔒 Access Control Gate (Demonstrating pv.stop())")
    access_key = pv.text_input("Enter Clearance Token", placeholder="Type 'admin' to unlock...", type="password")

    if access_key != "admin":
        pv.warning("Access restricted. Please provide a valid clearance token to view sensitive operations.")
        pv.write("Execution is halted below this line using `pv.stop()`.")
        pv.stop()

    # Code below only executes if clearance token matches
    pv.success("Clearance verified! Privileged diagnostic tools unlocked.")
    pv.write("Executing root administration diagnostic commands...")
    col1, col2 = pv.columns(2)
    with col1:
        pv.metric("Security Level", "Tier 1 - Root", "+Full Clearance")
    with col2:
        pv.metric("Audit Status", "Compliant", "Zero Violations")

elif nav_choice == "pipeline":
    pv.header("🧠 Singleton Neural Pipeline (@pv.cache_resource)")
    engine = get_inference_engine()
    
    col_a, col_b = pv.columns(2)
    with col_a:
        pv.metric("Pipeline Version", engine.model_version)
    with col_b:
        pv.metric("Engine Initialized At", engine.load_time, "Shared Singleton")
    
    pv.info("This resource is instantiated once globally and reused across all connected sessions.")

else:
    pv.header("📊 Cached Telemetry Stream (@pv.cache_data)")
    records = generate_telemetry_records(active_cluster, sample_limit)
    
    pv.dataframe(
        records,
        use_container_width=True,
    )
    pv.success(f"Telemetry stream loaded for **{active_cluster}** (Memoized cache active).")
