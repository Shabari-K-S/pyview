import datetime
import pytest
from pyview.context import ExecutionContext, reset_current_context, set_current_context
from pyview.runtime import Session
from pyview.uploads import UploadedFile
import pyview as pv


@pytest.fixture
def session():
    return Session(session_id="test_inputs_session")


def test_radio_resolution(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        # Default index
        val = pv.radio("Choose flavor", ["Vanilla", "Chocolate", "Strawberry"], index=1)
        assert val == "Chocolate"

        # Check element registered
        elements = ctx.get_serialized_elements()
        assert len(elements) == 1
        el = elements[0]
        assert el["type"] == "radio"
        assert el["props"]["options"] == ["Vanilla", "Chocolate", "Strawberry"]
        assert el["props"]["selected_index"] == 1
    finally:
        reset_current_context(token)


def test_multiselect_resolution(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        options = ["Python", "TypeScript", "Rust", "Go"]
        res = pv.multiselect("Skills", options, default=["Python", "Rust"])
        assert res == ["Python", "Rust"]

        elements = ctx.get_serialized_elements()
        el = elements[0]
        assert el["type"] == "multiselect"
        assert el["props"]["selected_indices"] == [0, 2]
    finally:
        reset_current_context(token)


def test_toggle_widget(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        val = pv.toggle("Enable notifications", value=True)
        assert val is True
        elements = ctx.get_serialized_elements()
        el = elements[0]
        assert el["type"] == "toggle"
        assert el["props"]["value"] is True
    finally:
        reset_current_context(token)


def test_color_picker(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        color = pv.color_picker("Brand Color", value="#ff5733")
        assert color == "#ff5733"
        elements = ctx.get_serialized_elements()
        el = elements[0]
        assert el["type"] == "color_picker"
        assert el["props"]["value"] == "#ff5733"
    finally:
        reset_current_context(token)


def test_feedback_widget(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        fb = pv.feedback("stars")
        assert fb is None
        elements = ctx.get_serialized_elements()
        el = elements[0]
        assert el["type"] == "feedback"
        assert el["props"]["feedback_type"] == "stars"
    finally:
        reset_current_context(token)


def test_segmented_control_and_pills(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        choice = pv.segmented_control("View mode", ["Grid", "List", "Kanban"], default="List")
        assert choice == "List"

        pills_choice = pv.pills("Tags", ["Bug", "Feature", "Docs"])
        assert pills_choice == "Bug"
    finally:
        reset_current_context(token)


def test_select_slider(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        tier = pv.select_slider("Select Plan", options=["Free", "Starter", "Pro", "Enterprise"], value="Pro")
        assert tier == "Pro"
        elements = ctx.get_serialized_elements()
        el = elements[0]
        assert el["type"] == "select_slider"
        assert el["props"]["selected_index"] == 2
    finally:
        reset_current_context(token)


def test_date_and_time_inputs(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        today = datetime.date(2026, 8, 29)
        d = pv.date_input("Event Date", value=today)
        assert d == today
        assert isinstance(d, datetime.date)

        t_val = datetime.time(14, 30, 0)
        t = pv.time_input("Start Time", value=t_val)
        assert t == t_val
        assert isinstance(t, datetime.time)

        elements = ctx.get_serialized_elements()
        assert elements[0]["props"]["value"] == "2026-08-29"
        assert elements[1]["props"]["value"] == "14:30:00"
    finally:
        reset_current_context(token)


def test_download_button_and_link_button(session):
    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        clicked = pv.download_button(
            label="Download Log",
            data="Log entry 1\nLog entry 2",
            file_name="app.log",
            mime="text/plain",
        )
        assert clicked is False

        elements = ctx.get_serialized_elements()
        el = elements[0]
        assert el["type"] == "download_button"
        assert el["props"]["file_name"] == "app.log"
        assert "data:text/plain;base64," in el["props"]["data_url"]

        pv.link_button("Documentation", url="https://pyview.dev")
        elements = ctx.get_serialized_elements()
        el2 = elements[1]
        assert el2["type"] == "link_button"
        assert el2["props"]["url"] == "https://pyview.dev"
    finally:
        reset_current_context(token)


def test_chat_input_transient_reset(session):
    # Simulate first rerun where user typed "Hello PyView!"
    ctx1 = ExecutionContext(
        session=session,
        active_triggers={"user_chat_box"},
        pending_values={"user_chat_box": "Hello PyView!"},
    )
    token1 = set_current_context(ctx1)
    try:
        prompt1 = pv.chat_input("Ask AI...", key="chat_box")
        assert prompt1 == "Hello PyView!"
    finally:
        reset_current_context(token1)

    # Next cycle without active trigger must evaluate to None
    ctx2 = ExecutionContext(session=session)
    token2 = set_current_context(ctx2)
    try:
        prompt2 = pv.chat_input("Ask AI...", key="chat_box")
        assert prompt2 is None
    finally:
        reset_current_context(token2)


def test_form_container_and_batch_submission(session):
    # 1. First run: form rendered, values initialized
    ctx1 = ExecutionContext(session=session)
    token1 = set_current_context(ctx1)
    try:
        with pv.form("booking_form"):
            name = pv.text_input("Name", value="Alice")
            guests = pv.number_input("Guests", value=2)
            submitted = pv.form_submit_button("Book Now")

            assert name == "Alice"
            assert guests == 2
            assert submitted is False

        # Verify form container in element tree
        serialized = ctx1.get_serialized_elements()
        assert len(serialized) == 1
        form_el = serialized[0]
        assert form_el["type"] == "form"
        assert len(form_el["children"]) == 3
        assert form_el["children"][0]["props"]["form_id"] == "user_booking_form"
        assert form_el["children"][1]["props"]["form_id"] == "user_booking_form"
        assert form_el["children"][2]["type"] == "form_submit_button"
    finally:
        reset_current_context(token1)

    # 2. Form submission run: batch submitted values arriving
    submit_btn_id = serialized[0]["children"][2]["id"]
    name_id = serialized[0]["children"][0]["id"]
    guests_id = serialized[0]["children"][1]["id"]

    ctx2 = ExecutionContext(
        session=session,
        active_triggers={submit_btn_id},
        pending_values={name_id: "Bob", guests_id: 4},
    )
    token2 = set_current_context(ctx2)
    try:
        with pv.form("booking_form"):
            name2 = pv.text_input("Name", value="Alice")
            guests2 = pv.number_input("Guests", value=2)
            submitted2 = pv.form_submit_button("Book Now")

            assert name2 == "Bob"
            assert guests2 == 4
            assert submitted2 is True
    finally:
        reset_current_context(token2)


def test_file_uploader_and_uploaded_file(session):
    # Prepare uploaded file in session
    file_obj = UploadedFile(
        name="sales_report.csv",
        size=1024,
        type="text/csv",
        content=b"Product,Sales\nA,100\nB,200\n",
    )
    session.uploaded_files["user_my_uploader"] = file_obj

    ctx = ExecutionContext(session=session)
    token = set_current_context(ctx)
    try:
        uploaded = pv.file_uploader("Upload Report", type=["csv"], key="my_uploader")
        assert uploaded is not None
        assert uploaded.name == "sales_report.csv"
        assert uploaded.size == 1024
        assert uploaded.getvalue() == b"Product,Sales\nA,100\nB,200\n"
        assert uploaded.read().decode("utf-8").startswith("Product,Sales")

        serialized = ctx.get_serialized_elements()
        assert len(serialized) == 1
        el = serialized[0]
        assert el["type"] == "file_uploader"
        assert el["props"]["has_file"] is True
        assert el["props"]["file_name"] == "sales_report.csv"
    finally:
        reset_current_context(token)


def test_fastapi_upload_endpoint_and_form_batch_e2e():
    """End-to-end test of REST multipart file upload route and WebSocket form submission."""
    from pathlib import Path
    from starlette.testclient import TestClient
    from pyview.server import create_app

    inputs_script = Path(__file__).parent.parent / "examples" / "inputs_showcase.py"
    app = create_app(inputs_script)
    client = TestClient(app)

    # 1. Connect WebSocket to establish session
    with client.websocket_connect("/_pyview/ws") as ws:
        def wait_for_render():
            render_msg = None
            while True:
                msg = ws.receive_json()
                if msg.get("type") == "render":
                    render_msg = msg
                elif msg.get("type") == "status" and msg.get("status") == "idle" and render_msg is not None:
                    return render_msg

        msg_conn = ws.receive_json()
        assert msg_conn["type"] == "connected"
        session_id = msg_conn["session_id"]

        init_render = wait_for_render()
        assert init_render is not None

        # 2. Upload file via REST endpoint POST /_pyview/upload/{session_id}/{key}
        file_payload = b"col1,col2\n100,200\n"
        upload_resp = client.post(
            f"/_pyview/upload/{session_id}/user_uploaded_rfp",
            files={"file": ("spec.csv", file_payload, "text/csv")},
        )
        assert upload_resp.status_code == 200
        upload_json = upload_resp.json()
        assert upload_json["status"] == "ok"
        assert upload_json["name"] == "spec.csv"

        def find_element_recursive(elements, type_name):
            for e in elements:
                if e.get("type") == type_name:
                    return e
                if "children" in e:
                    res = find_element_recursive(e["children"], type_name)
                    if res:
                        return res
            return None

        # Find submit button ID dynamically
        submit_btn_node = find_element_recursive(init_render["elements"], "form_submit_button")
        assert submit_btn_node is not None
        submit_btn_id = submit_btn_node["id"]
        form_id = submit_btn_node["props"]["form_id"]

        # 3. Submit form batch via WebSocket
        ws.send_json({
            "type": "form_submit",
            "form_id": form_id,
            "submit_key": submit_btn_id,
            "values": {},
        })

        # Receive updated render with success message and download button
        msg_render_submitted = wait_for_render()
        assert msg_render_submitted is not None

        success_el = find_element_recursive(msg_render_submitted["elements"], "alert")
        assert success_el is not None
        assert "Elena Rostova" in success_el["props"]["text"]
        assert "Priority" in success_el["props"]["text"]

        # Find download button with embedded Base64 data
        dl_btn = find_element_recursive(msg_render_submitted["elements"], "download_button")
        assert dl_btn is not None
        assert "data:text/plain;base64," in dl_btn["props"]["data_url"]

        # 4. Test chat input submission
        chat_node = find_element_recursive(init_render["elements"], "chat_input")
        assert chat_node is not None
        chat_id = chat_node["id"]

        ws.send_json({
            "type": "widget_event",
            "key": chat_id,
            "value": "What is the turnaround time?",
            "is_trigger": True,
        })

        # Receive new render
        msg_chat_render = wait_for_render()
        assert msg_chat_render is not None
        assert any(
            "What is the turnaround time?" in str(e)
            for e in msg_chat_render["elements"]
        )



