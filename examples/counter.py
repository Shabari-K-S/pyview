"""Interactive Counter Application."""

import pyview as pv

# Initialize session state
if "count" not in pv.session_state:
    pv.session_state.count = 0

if "history" not in pv.session_state:
    pv.session_state.history = []

if "last_delta" not in pv.session_state:
    pv.session_state.last_delta = None

# Main Page Header
pv.title("🎛️ Interactive Counter")
pv.write("A clean reactive counter with customizable step size and live delta tracking.")

# Step Size Configuration
step = pv.number_input(
    "Step Size",
    min_value=1,
    max_value=100,
    value=1,
    key="step_size",
)

# Action Buttons
with pv.card("Actions"):
    c1, c2, c3 = pv.columns([1, 1, 1])
    
    with c1:
        if pv.button(f"➕ Increment (+{step})", key="btn_inc"):
            pv.session_state.count += int(step)
            pv.session_state.last_delta = f"+{step}"
            pv.session_state.history.append(f"Added {step} -> Total: {pv.session_state.count}")
            
    with c2:
        if pv.button(f"➖ Decrement (-{step})", key="btn_dec"):
            pv.session_state.count -= int(step)
            pv.session_state.last_delta = f"-{step}"
            pv.session_state.history.append(f"Subtracted {step} -> Total: {pv.session_state.count}")
            
    with c3:
        if pv.button("🔄 Reset", key="btn_reset"):
            pv.session_state.count = 0
            pv.session_state.last_delta = "0"
            pv.session_state.history.append("Reset counter to 0")

# Header & Metric Display
pv.header(f"Current Count: {pv.session_state.count}")

col_m1, col_m2 = pv.columns([1, 1])
with col_m1:
    pv.metric("Total Count", f"{pv.session_state.count:,}", delta=pv.session_state.last_delta)
with col_m2:
    pv.metric("Step Increment", str(step))

pv.divider()

# Recent Activity Log
pv.header(f"Recent Activity ({len(pv.session_state.history)})")
if pv.session_state.history:
    for entry in reversed(pv.session_state.history[-5:]):
        pv.write(f"- ⏱️ {entry}")
    if pv.button("🗑️ Clear History", key="btn_clear_hist"):
        pv.session_state.history = []
else:
    pv.write("_No actions recorded yet. Click a button above to start counting!_")