"""Executive SaaS Performance & Operations Dashboard."""

import pyview as pv

# Sidebar: Region Selection & Global Controls
with pv.sidebar:
    pv.title("⚙️ Dashboard Controls")
    
    region = pv.selectbox(
        "Operating Region",
        options=["Global Overview", "North America (US-East)", "Europe (EU-Central)", "Asia-Pacific (AP-South)"],
        index=0,
        key="selected_region",
    )
    
    enable_alerts = pv.checkbox(
        "Real-Time Anomaly Alerts",
        value=True,
        key="chk_alerts",
    )
    
    refresh_rate = pv.slider(
        "Data Refresh Rate (sec)",
        min_value=1,
        max_value=30,
        value=5,
        key="slider_polling",
    )
    
    pv.divider()
    pv.write(f"_Region: **{region}**_")
    pv.write(f"_Polling Frequency: **{refresh_rate}s**_")
    
    if pv.button("🔄 Reset Defaults", key="btn_reset_dash"):
        pv.session_state.selected_region = "Global Overview"
        pv.session_state.chk_alerts = True
        pv.session_state.slider_growth = 25
        pv.session_state.budget_input = 85

# Main Header
pv.title("📊 Executive Performance Dashboard")
pv.write(f"Displaying real-time revenue, customer churn, and latency metrics for **{region}**.")

# 4-Column KPI Metric Row
k1, k2, k3, k4 = pv.columns([1, 1, 1, 1])
with k1:
    pv.metric("Total Revenue", "$148,200", delta="+12.4%", delta_color="normal")
with k2:
    pv.metric("Subscriptions", "4,890", delta="+310", delta_color="normal")
with k3:
    pv.metric("Churn Rate", "1.8%", delta="-0.4%", delta_color="inverse")
with k4:
    pv.metric("P99 Latency", "165ms", delta="+24ms", delta_color="inverse")

pv.divider()

# Tabbed Dashboard Sections
tab_overview, tab_budget, tab_health = pv.tabs([
    "📈 Executive Summary",
    "💼 Budget & Planning",
    "🩺 Service Health",
])

# --- Tab 1: Executive Summary ---
with tab_overview:
    col_g, col_s = pv.columns([3, 2])
    
    with col_g:
        pv.header("🎯 Growth Targets & Operational Alerting")
        
        growth_threshold = pv.slider(
            "Quarterly Growth Target (%)",
            min_value=0,
            max_value=100,
            value=25,
            step=5,
            key="slider_growth",
        )
        
        if growth_threshold >= 50:
            pv.warning(f"Growth target set to an aggressive **{growth_threshold}%**! Ensure adequate infrastructure bandwidth.")
        else:
            pv.info(f"Growth target configured at standard pace of **{growth_threshold}%**.")
            
        if enable_alerts:
            pv.success("Real-time automated anomaly detection is **Active** across all microservices.")
        else:
            pv.error("Anomaly detection alerts are currently **Disabled**! System risks unmonitored failures.")

    with col_s:
        with pv.card("📍 Region Snapshot"):
            pv.write(f"- Active Region: **{region}**")
            pv.write(f"- Target Growth: **{growth_threshold}%**")
            pv.write(f"- Monitoring Status: **{'Online' if enable_alerts else 'Offline'}**")
            pv.write(f"- Polling Interval: **{refresh_rate}s**")

# --- Tab 2: Budget & Planning ---
with tab_budget:
    with pv.card("Marketing Budget Allocation"):
        c_b1, c_b2 = pv.columns([1, 1])
        with c_b1:
            budget_k = pv.number_input(
                "Monthly Marketing Budget ($k)",
                min_value=10,
                max_value=500,
                value=85,
                step=5,
                key="budget_input",
            )
            pv.metric("Annualized Allocation", f"${budget_k * 12:,}k / yr")
        with c_b2:
            notes = pv.text_area(
                "Executive Planning Notes",
                value="Prioritize enterprise onboarding and reduce edge latency.",
                key="exec_notes",
            )

# --- Tab 3: Service Health ---
with tab_health:
    with pv.card("Microservice Cluster Health"):
        h1, h2 = pv.columns([1, 1])
        with h1:
            pv.write("- 🟢 `auth-service`: Healthy (p99: 38ms)")
            pv.write("- 🟢 `billing-gateway`: Healthy (p99: 82ms)")
        with h2:
            pv.write("- 🟢 `analytics-worker`: Healthy (lag: 0.1s)")
            pv.write("- 🟢 `edge-ingress`: Healthy (42k req/sec)")
            
    with pv.expander("🔍 Detailed Telemetry Overview", expanded=False):
        pv.write({
            "Region": region,
            "Monitoring Alerts": enable_alerts,
            "Target Growth": f"{growth_threshold}%",
            "Monthly Budget": f"${budget_k}k",
        })
