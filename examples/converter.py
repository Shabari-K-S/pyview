"""Universal Scientific & Unit Measurement Converter."""

import pyview as pv

# Initialize session state
if "history" not in pv.session_state:
    pv.session_state.history = [
        "Temperature: 25.00°C = 77.00°F = 298.15K",
        "Distance: 10.00 km = 6.21 mi (10,000 m)",
    ]

# Main Header
pv.title("📐 Universal Unit Converter")
pv.write("Convert temperatures, distances, and weights with real-time mathematical calculations.")

# Precision Settings Bar
col_prec, col_count = pv.columns([3, 1])
with col_prec:
    precision = pv.slider(
        "Calculation Precision (Decimal Places)",
        min_value=1,
        max_value=6,
        value=2,
        key="sb_precision",
    )
with col_count:
    pv.metric("Saved Conversions", str(len(pv.session_state.history)))

pv.divider()

# Tabbed Measurement Domains
tab_temp, tab_dist, tab_weight, tab_history = pv.tabs([
    "🌡️ Temperature",
    "📏 Distance & Length",
    "⚖️ Weight & Mass",
    f"📜 Saved History ({len(pv.session_state.history)})",
])

# --- Tab 1: Temperature ---
with tab_temp:
    col_t_in, col_t_out = pv.columns([1, 1])
    
    with col_t_in:
        with pv.card("Input Temperature"):
            temp_c = pv.number_input(
                "Temperature in Celsius (°C)",
                value=25.0,
                step=1.0,
                key="num_celsius",
            )
            
            f_val = (temp_c * 9 / 5) + 32
            k_val = temp_c + 273.15
            
            if pv.button("💾 Save Temperature", key="btn_save_temp"):
                pv.session_state.history.append(
                    f"Temperature: {temp_c:.{precision}f}°C = {f_val:.{precision}f}°F = {k_val:.{precision}f}K"
                )
                pv.success("Temperature conversion logged to saved history.")

    with col_t_out:
        with pv.card(f"Results for {temp_c:.{precision}f} °C"):
            c_f, c_k = pv.columns([1, 1])
            with c_f:
                pv.metric("Fahrenheit", f"{f_val:.{precision}f} °F")
            with c_k:
                pv.metric("Kelvin", f"{k_val:.{precision}f} K")
            pv.divider()
            pv.write(f"- Standard Formula: `(°C × 9/5) + 32`")
            pv.write(f"- Absolute Zero Delta: `{k_val - 273.15:.2f}°C from 0K`")

# --- Tab 2: Distance ---
with tab_dist:
    col_d_in, col_d_out = pv.columns([1, 1])
    
    with col_d_in:
        with pv.card("Input Distance"):
            dist_km = pv.number_input(
                "Distance in Kilometers (km)",
                min_value=0.0,
                value=10.0,
                step=1.0,
                key="num_km",
            )
            
            miles = dist_km * 0.621371
            meters = dist_km * 1000
            feet = dist_km * 3280.84
            
            if pv.button("💾 Save Distance", key="btn_save_dist"):
                pv.session_state.history.append(
                    f"Distance: {dist_km:.{precision}f} km = {miles:.{precision}f} mi ({meters:,.0f} m)"
                )
                pv.success("Distance conversion logged to saved history.")

    with col_d_out:
        with pv.card(f"Results for {dist_km:.{precision}f} km"):
            c_mi, c_m = pv.columns([1, 1])
            with c_mi:
                pv.metric("Miles", f"{miles:.{precision}f} mi")
            with c_m:
                pv.metric("Meters", f"{meters:,.0f} m")
            pv.metric("Feet", f"{feet:,.{precision}f} ft")

# --- Tab 3: Weight ---
with tab_weight:
    col_w_in, col_w_out = pv.columns([1, 1])
    
    with col_w_in:
        with pv.card("Input Weight"):
            weight_kg = pv.number_input(
                "Weight in Kilograms (kg)",
                min_value=0.0,
                value=70.0,
                step=0.5,
                key="num_kg",
            )
            
            lbs = weight_kg * 2.20462
            grams = weight_kg * 1000
            oz = weight_kg * 35.274
            
            if pv.button("💾 Save Weight", key="btn_save_weight"):
                pv.session_state.history.append(
                    f"Weight: {weight_kg:.{precision}f} kg = {lbs:.{precision}f} lbs ({grams:,.0f} g)"
                )
                pv.success("Weight conversion logged to saved history.")

    with col_w_out:
        with pv.card(f"Results for {weight_kg:.{precision}f} kg"):
            c_lb, c_oz = pv.columns([1, 1])
            with c_lb:
                pv.metric("Pounds", f"{lbs:.{precision}f} lbs")
            with c_oz:
                pv.metric("Ounces", f"{oz:.{precision}f} oz")
            pv.metric("Grams", f"{grams:,.0f} g")

# --- Tab 4: Saved History ---
with tab_history:
    col_h_hdr, col_h_btn = pv.columns([3, 1])
    with col_h_hdr:
        pv.header(f"Conversion History ({len(pv.session_state.history)})")
    with col_h_btn:
        pv.write("") # spacing
        if pv.session_state.history and pv.button("🗑️ Clear History", key="btn_clear_history"):
            pv.session_state.history = []

    if pv.session_state.history:
        for item in reversed(pv.session_state.history[-8:]):
            pv.write(f"- 📌 {item}")
    else:
        pv.info("No conversions saved in this session yet.")
