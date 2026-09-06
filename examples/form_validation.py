"""User Registration & Community Member Directory."""

import re
import pyview as pv

# Initialize session state
if "registered_users" not in pv.session_state:
    pv.session_state.registered_users = [
        {"name": "Ada Lovelace", "email": "ada@analytical.org", "age": 36, "role": "Lead Architect", "tier": "Enterprise Tier"},
        {"name": "Alan Turing", "email": "alan@enigma-lab.io", "age": 41, "role": "Systems Engineer", "tier": "Enterprise Tier"},
        {"name": "Grace Hopper", "email": "grace@compiler.net", "age": 52, "role": "Principal Scientist", "tier": "Professional Tier"},
    ]

users = pv.session_state.registered_users

# Main Header
pv.title("📝 Developer Community Portal")
pv.write("Register new community members, manage credentials, and browse active profiles.")

# Top Metric Summary
col_m1, col_m2, col_m3 = pv.columns([1, 1, 1])
with col_m1:
    pv.metric("Total Members", str(len(users)), delta=f"+{len(users)}", delta_color="normal")
with col_m2:
    enterprise_count = sum(1 for u in users if u.get("tier") == "Enterprise Tier")
    pv.metric("Enterprise Tier", str(enterprise_count))
with col_m3:
    std_count = len(users) - enterprise_count
    pv.metric("Standard Tier", str(std_count))

pv.divider()

# Tabbed Layout: Registration vs Directory
tab_register, tab_directory = pv.tabs([
    "✍️ Member Registration",
    f"👥 Community Directory ({len(users)})",
])

# --- Tab 1: Registration ---
with tab_register:
    with pv.card("New Member Registration"):
        col1, col2 = pv.columns([1, 1])
        
        with col1:
            name = pv.text_input("Full Name", key="input_name", placeholder="e.g. Margaret Hamilton")
            email = pv.text_input("Work Email", key="input_email", placeholder="e.g. margaret@nasa.gov")
            
        with col2:
            age = pv.number_input("Age", min_value=1, max_value=120, value=28, key="input_age")
            role = pv.selectbox(
                "Primary Role",
                options=["Software Engineer", "Systems Architect", "Data Scientist", "DevOps Engineer", "Product Manager"],
                index=0,
                key="sel_role",
            )
            
        col_tier, col_terms = pv.columns([1, 1])
        with col_tier:
            tier = pv.selectbox(
                "Membership Tier",
                options=["Standard Tier", "Professional Tier", "Enterprise Tier"],
                index=1,
                key="sel_tier",
            )
        with col_terms:
            pv.write("") # layout spacing
            accept_terms = pv.checkbox("I agree to the Community Guidelines & Terms of Service", value=False, key="chk_terms")
            
        pv.divider()
        
        if pv.button("🚀 Register Member", key="btn_submit_reg"):
            errors = []
            
            if not name.strip() or len(name.strip()) < 2:
                errors.append("Full Name must contain at least 2 characters.")
                
            email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            if not email.strip():
                errors.append("Work Email address is required.")
            elif not re.match(email_pattern, email.strip()):
                errors.append("Invalid email address format.")
                
            if age < 18 or age > 100:
                errors.append("Age must be between 18 and 100.")
                
            if not accept_terms:
                errors.append("You must agree to the Community Guidelines & Terms of Service.")
                
            if errors:
                for err in errors:
                    pv.error(f"**Validation Issue**: {err}")
            else:
                new_member = {
                    "name": name.strip(),
                    "email": email.strip(),
                    "age": int(age),
                    "role": role,
                    "tier": tier,
                }
                pv.session_state.registered_users.append(new_member)
                pv.success(f"🎉 **{name.strip()}** successfully registered as **{role}** ({tier})!")

# --- Tab 2: Directory ---
with tab_directory:
    col_hdr, col_rst = pv.columns([3, 1])
    with col_hdr:
        pv.header(f"Registered Members ({len(users)})")
    with col_rst:
        pv.write("") # spacing
        if users and pv.button("🗑️ Reset Directory", key="btn_reset_dir"):
            pv.session_state.registered_users = []
    
    if not users:
        pv.info("No members registered yet. Use the registration form to add members.")
    else:
        for idx, u in enumerate(users, start=1):
            with pv.card(f"#{idx}: {u['name']}"):
                c_email, c_role, c_tier = pv.columns([2, 2, 1])
                with c_email:
                    pv.write(f"📧 `{u['email']}`")
                with c_role:
                    pv.write(f"💼 **{u['role']}** (Age: {u['age']})")
                with c_tier:
                    pv.write(f"⭐ _{u.get('tier', 'Standard')}_")
