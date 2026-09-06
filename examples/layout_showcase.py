"""Cloud Infrastructure Operations & Scaling Portal."""

import pyview as pv

# 1. Sidebar: Environment & Region Settings
with pv.sidebar:
    pv.title("🛠️ Cloud Control Center")
    
    app_mode = pv.selectbox(
        "Deployment Environment",
        options=["Production Cluster", "Staging Environment", "Development Cluster"],
        index=0,
        key="sb_app_mode",
    )
    
    data_region = pv.selectbox(
        "Operating Region",
        options=["Global (US + EU + AP)", "US-East (N. Virginia)", "EU-West (Frankfurt)", "AP-South (Tokyo)"],
        index=0,
        key="sb_region",
    )
    
    refresh_rate = pv.slider(
        "Metrics Polling (sec)",
        min_value=1,
        max_value=60,
        value=10,
        key="sb_refresh_rate",
    )
    
    enable_debug = pv.checkbox(
        "Enable Verbose Telemetry",
        value=False,
        key="sb_debug",
    )
    
    pv.divider()
    pv.write(f"_Region: **{data_region}**_")
    pv.write(f"_Polling Interval: **{refresh_rate}s**_")

# 2. Main Page Header
pv.title("🏢 Cloud Infrastructure Portal")
pv.write(f"Active Environment: **{app_mode}** | Data Center: **{data_region}**")

# 3. Top Metrics Row
col1, col2, col3, col4 = pv.columns([1, 1, 1, 1])
with col1:
    pv.metric("Total Clusters", "24", delta="+3", delta_color="normal")
with col2:
    pv.metric("Active Pods", "1,842", delta="+120", delta_color="normal")
with col3:
    pv.metric("Avg Latency", "138ms", delta="-12ms", delta_color="inverse")
with col4:
    pv.metric("Error Budget", "99.95%", delta="+0.02%", delta_color="normal")

pv.divider()

# 4. Multi-Tabbed Views
tab_forecast, tab_config, tab_health = pv.tabs([
    "📊 Workload & Scaling Forecast",
    "⚙️ Node Pool Configuration",
    "🩺 Service Health & Diagnostics",
])

# --- Tab 1: Workload Forecast ---
with tab_forecast:
    pv.header("📈 Traffic Simulation & Resource Scaling")
    
    col_left, col_right = pv.columns([3, 2])
    
    with col_left:
        with pv.card("Simulation Parameters"):
            target_load = pv.slider(
                "Simulated Traffic Surge (%)",
                min_value=0,
                max_value=300,
                value=50,
                step=10,
                key="slider_traffic",
            )
            
            replicas = pv.number_input(
                "Base Replicas",
                min_value=2,
                max_value=100,
                value=8,
                key="num_replicas",
            )
            
            calculated_pods = int(replicas * (1 + target_load / 100))
            estimated_cost = calculated_pods * 45
            
            if target_load >= 150:
                pv.warning(f"Surge of **{target_load}%** requires **{calculated_pods} pods**. Verify node pool autoscaling limits!")
            else:
                pv.success(f"Cluster capacity optimal: **{calculated_pods} pods** will handle **+{target_load}%** traffic.")
                
    with col_right:
        with pv.card("Resource & Cost Projections"):
            pv.metric("Projected Pods", f"{calculated_pods} pods", delta=f"+{calculated_pods - replicas}")
            pv.metric("Estimated Cost", f"${estimated_cost:,} / mo", delta=f"+${(calculated_pods - replicas) * 45:,}", delta_color="inverse")
            pv.divider()
            pv.write(f"- Base Replicas: **{replicas}**")
            pv.write(f"- Scaling Factor: **{(1 + target_load / 100):.1f}x**")

# --- Tab 2: Node Pool Configuration ---
with tab_config:
    with pv.card("Node Pool Specifications"):
        node_type = pv.selectbox(
            "Compute Instance Type",
            options=["c6i.2xlarge (8 vCPU, 16GB RAM)", "m6i.4xlarge (16 vCPU, 64GB RAM)", "r6i.8xlarge (32 vCPU, 256GB RAM)"],
            index=0,
            key="sel_node_type",
        )
        
        cluster_notes = pv.text_area(
            "Maintenance Notes & Change Log",
            value="Rolling node upgrade scheduled for Sunday 02:00 UTC.",
            key="txt_notes",
        )
        
        if pv.button("💾 Apply Configuration", key="btn_apply_config"):
            pv.success(f"Configuration applied! Selected instance type: **{node_type}**")

# --- Tab 3: Service Health ---
with tab_health:
    with pv.expander("🩺 Microservice Status Breakdown", expanded=True):
        pv.write("- 🟢 `auth-service`: 12/12 pods healthy (p99: 42ms)")
        pv.write("- 🟢 `billing-api`: 8/8 pods healthy (p99: 95ms)")
        pv.write("- 🟢 `data-pipeline`: 24/24 pods healthy (lag: 0.2s)")
        pv.write("- 🟢 `ingress-nginx`: 6/6 pods healthy (45k req/sec)")
        
    with pv.expander("🔍 Telemetry Payload", expanded=False):
        pv.write({
            "environment": app_mode,
            "region": data_region,
            "active_pods": calculated_pods,
            "instance_type": node_type,
            "verbose_logging": enable_debug,
        })
