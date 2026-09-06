"""Comprehensive Input Widgets & Form Batching Showcase for PyView.

Demonstrates:
- Batch Form submission with `pv.form` and `pv.form_submit_button`
- Temporal pickers (`pv.date_input`, `pv.time_input`)
- Selection & pills controls (`pv.radio`, `pv.multiselect`, `pv.segmented_control`, `pv.pills`, `pv.select_slider`)
- Modern toggles & switches (`pv.toggle`)
- Interactive feedback ratings (`pv.feedback` stars, thumbs, faces)
- Visual styling & color picker (`pv.color_picker`)
- File uploads & downloads (`pv.file_uploader`, `pv.download_button`, `pv.link_button`)
- Conversational chat input (`pv.chat_input`)
"""

import datetime
import pyview as pv

pv.title("OmniDesk Service & Consultation Portal")
pv.write(
    "Experience next-generation reactive PyView input widgets with seamless form batching, "
    "temporal pickers, rich rating sentiment controls, and client-side download capabilities."
)

if "chat_messages" not in pv.session_state:
    pv.session_state.chat_messages = [
        {"role": "assistant", "text": "Welcome to OmniDesk Support! How can I assist your consultation booking today?"}
    ]

# Layout Tabs
tab_booking, tab_feedback, tab_chat, tab_customizer = pv.tabs(
    ["🗓️ Service Booking Form", "⭐ Experience Rating", "💬 Live AI Assistant", "🎨 Portal Customizer"]
)

with tab_booking:
    pv.header("Book a Consultation Session")
    pv.write("Inputs inside this batch form are collected client-side and submitted in a single reactive transaction.")

    with pv.form("booking_portal_form"):
        col1, col2 = pv.columns([1, 1])
        with col1:
            name = pv.text_input("Full Name", value="Elena Rostova", placeholder="Your name")
            email = pv.text_input("Work Email", value="elena@cloudmatrix.io", placeholder="name@company.com")
            service_tier = pv.segmented_control(
                "Service Level",
                ["Standard", "Priority", "VIP Executive"],
                default="Priority",
            )
            consult_date = pv.date_input("Preferred Date", value=datetime.date.today() + datetime.timedelta(days=2))

        with col2:
            contact_pref = pv.radio("Preferred Communication Channel", ["Video Call", "Phone", "In-Person"], index=0, horizontal=True)
            consult_time = pv.time_input("Session Time", value=datetime.time(10, 30))
            topics = pv.multiselect(
                "Discussion Topics",
                ["Architecture Design", "Security Audit", "Performance Optimization", "Data Pipelines"],
                default=["Architecture Design", "Performance Optimization"],
            )
            budget_tier = pv.select_slider("Project Scale ($)", options=["< $10k", "$10k - $50k", "$50k - $200k", "$200k+"], value="$50k - $200k")

        notes = pv.text_area("Additional Requirements", placeholder="Tell us more about your infrastructure...", height=80)
        nda_req = pv.toggle("Request Non-Disclosure Agreement (NDA)", value=True)
        uploaded_rfp = pv.file_uploader("Upload RFP Document (Optional)", type=["pdf", "csv", "txt", "docx"])

        submitted = pv.form_submit_button("Confirm & Book Consultation")

    if submitted:
        pv.success(f"Consultation Request Confirmed for **{name}** ({service_tier} Tier)!")
        confirmation_doc = (
            f"--- OMNIDESK BOOKING RECEIPT ---\n"
            f"Client: {name}\n"
            f"Email: {email}\n"
            f"Tier: {service_tier}\n"
            f"Channel: {contact_pref}\n"
            f"Date & Time: {consult_date} at {consult_time}\n"
            f"Topics: {', '.join(topics)}\n"
            f"Budget: {budget_tier}\n"
            f"NDA: {'Yes' if nda_req else 'No'}\n"
            f"Uploaded File: {uploaded_rfp.name if uploaded_rfp else 'None'}\n"
            f"Notes: {notes}\n"
        )
        pv.download_button(
            label="Download Booking Confirmation (TXT)",
            data=confirmation_doc,
            file_name=f"booking_{name.lower().replace(' ', '_')}.txt",
            mime="text/plain",
        )

with tab_feedback:
    pv.header("Service Experience & Sentiment Feedback")
    pv.write("Real-time sentiment captures with native star, thumb, and facial emotion meters.")

    fcol1, fcol2, fcol3 = pv.columns([1, 1, 1])

    with fcol1:
        with pv.card("Overall Satisfaction"):
            stars = pv.feedback("stars", key="star_rating")
            if stars:
                pv.info(f"You rated: **{stars} / 5 Stars**")

    with fcol2:
        with pv.card("Recommendation Likelihood"):
            thumbs = pv.feedback("thumbs", key="thumb_rating")
            if thumbs is not None:
                pv.write("👍 Positive" if thumbs == 1 else "👎 Needs Improvement")

    with fcol3:
        with pv.card("Platform Speed & Ease"):
            faces = pv.feedback("faces", key="face_rating")
            if faces:
                labels = ["Very Frustrated", "Disappointed", "Neutral", "Pleased", "Delighted!"]
                pv.write(f"Mood: **{labels[faces - 1]}**")

    pv.divider()
    feedback_tags = pv.pills("Quick Tags", ["Blazing Fast", "Intuitive UI", "Great Support", "Needs Dark Mode"])
    pv.write(f"Active Tag: `{feedback_tags}`")

with tab_chat:
    pv.header("Real-Time AI Consultation Assistant")

    prompt = pv.chat_input("Type your question for the AI consultant...", key="support_chat_box")
    if prompt:
        pv.session_state.chat_messages.append({"role": "user", "text": prompt})
        pv.session_state.chat_messages.append({
            "role": "assistant",
            "text": f"Thank you for asking about: '{prompt}'. Our lead engineer has been notified and scheduled for your review.",
        })

    for msg in pv.session_state.chat_messages:
        with pv.card():
            prefix = "🤖 **OmniAI**" if msg["role"] == "assistant" else "👤 **You**"
            pv.write(f"{prefix}: {msg['text']}")


with tab_customizer:
    pv.header("Personalize Your Brand Experience")

    col_c1, col_c2 = pv.columns([1, 1])
    with col_c1:
        brand_color = pv.color_picker("Accent Color", value="#238636")
        dark_preset = pv.toggle("High Contrast Mode", value=False)
        pv.write(f"Selected Palette: `<span style='color: {brand_color}; font-weight: bold;'>{brand_color}</span>`")

    with col_c2:
        pv.write("### Helpful Quick Links")
        pv.link_button("View GitHub Repository", url="https://github.com")
        pv.link_button("Read API Documentation", url="https://pyview.dev")
