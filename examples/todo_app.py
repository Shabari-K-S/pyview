"""Daily Task & Productivity Manager."""

import pyview as pv

# Initialize session state
if "todos" not in pv.session_state:
    pv.session_state.todos = [
        {"id": 1, "text": "Review architecture design document", "done": True, "priority": "High"},
        {"id": 2, "text": "Implement client-side tab switcher", "done": True, "priority": "Medium"},
        {"id": 3, "text": "Set up automated integration test suite", "done": False, "priority": "High"},
        {"id": 4, "text": "Publish release notes for v0.1.0", "done": False, "priority": "Low"},
    ]
if "next_id" not in pv.session_state:
    pv.session_state.next_id = 5

todos = pv.session_state.todos

# Main Header
pv.title("✅ Daily Task Planner")
pv.write("Stay organized, prioritize essential work, and track your daily productivity.")

# Top KPI Metric Strip
total = len(todos)
completed = sum(1 for t in todos if t["done"])
pending = total - completed
rate = f"{(completed / total * 100):.0f}%" if total > 0 else "0%"

m1, m2, m3, m4 = pv.columns([1, 1, 1, 1])
with m1:
    pv.metric("Total Tasks", str(total))
with m2:
    pv.metric("Completed", str(completed), delta=f"+{completed}", delta_color="normal")
with m3:
    pv.metric("Pending", str(pending), delta=f"{pending}", delta_color="inverse")
with m4:
    pv.metric("Completion Rate", rate, delta=rate, delta_color="normal")

pv.divider()

# Add Task Card
with pv.card("➕ Create New Task"):
    col_desc, col_prio, col_btn = pv.columns([4, 2, 1])
    with col_desc:
        new_title = pv.text_input("Task Description", value="", key="input_task_desc", placeholder="e.g. Schedule sprint retrospective...")
    with col_prio:
        new_prio = pv.selectbox("Priority", options=["High", "Medium", "Low"], index=1, key="sel_new_prio")
    with col_btn:
        pv.write("") # layout alignment
        if pv.button("Add Task", key="btn_add_task"):
            clean = new_title.strip()
            if clean:
                pv.session_state.todos.append({
                    "id": pv.session_state.next_id,
                    "text": clean,
                    "done": False,
                    "priority": new_prio,
                })
                pv.session_state.next_id += 1
                pv.session_state.input_task_desc = ""
                pv.success(f"Added '**{clean}**' to your list.")
            else:
                pv.warning("Please enter a task description before adding.")

# Filter and Bulk Action Controls
col_filter, col_bulk = pv.columns([2, 1])
with col_filter:
    view_filter = pv.selectbox(
        "Filter Tasks",
        options=["All Tasks", "Pending Only", "Completed Only"],
        index=0,
        key="filter_status",
    )
with col_bulk:
    pv.write("") # alignment
    b1, b2 = pv.columns([1, 1])
    with b1:
        if pv.button("✔️ Complete All", key="btn_mark_all_done"):
            for t in todos:
                t["done"] = True
    with b2:
        if pv.button("🧹 Clear Done", key="btn_clear_completed"):
            pv.session_state.todos = [t for t in todos if not t["done"]]

# Filter Visible Tasks
visible_todos = todos
if view_filter == "Pending Only":
    visible_todos = [t for t in visible_todos if not t["done"]]
elif view_filter == "Completed Only":
    visible_todos = [t for t in visible_todos if t["done"]]

# Task List
pv.header(f"Tasks ({len(visible_todos)})")

if not visible_todos:
    if total == 0:
        pv.info("Your task list is empty! Use the form above to add your first task.")
    else:
        pv.info(f"No tasks found matching filter: **{view_filter}**.")
else:
    for t in visible_todos:
        c_text, c_badge, c_toggle, c_del = pv.columns([5, 2, 2, 1])
        
        with c_text:
            icon = "✅" if t["done"] else "⏳"
            text_formatted = f"~~{t['text']}~~" if t["done"] else f"**{t['text']}**"
            pv.write(f"{icon} {text_formatted}")
            
        with c_badge:
            badge_map = {"High": "🔴 High", "Medium": "🟡 Medium", "Low": "🟢 Low"}
            pv.write(f"_{badge_map.get(t.get('priority', 'Medium'), 'Medium')}_")
            
        with c_toggle:
            label = "↩️ Mark Pending" if t["done"] else "✔️ Mark Done"
            if pv.button(label, key=f"btn_tog_{t['id']}"):
                t["done"] = not t["done"]
                break
                
        with c_del:
            if pv.button("🗑️", key=f"btn_del_{t['id']}"):
                pv.session_state.todos = [x for x in todos if x["id"] != t["id"]]
                break
