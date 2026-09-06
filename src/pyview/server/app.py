"""FastAPI backend and WebSocket transport for PyView.

Serves the single-page frontend, manages WebSocket lifecycles, and transports
element-tree JSON payloads between the Python runtime and the browser client.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import time
import uuid
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pyview.core.runtime import ScriptRunner, SessionManager, execute_session_run
from pyview.server.uploads import UploadedFile

STATIC_DIR = Path(__file__).parent.parent / "static"


def create_app(script_path: str | Path) -> FastAPI:
    """Create and configure the FastAPI application for the given user script."""
    app = FastAPI(title="PyView Server", docs_url=None, redoc_url=None)
    runner = ScriptRunner(script_path)
    session_manager = SessionManager()

    # Mount static assets directory
    if STATIC_DIR.exists():
        app.mount("/_pyview/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def index() -> FileResponse:
        """Serve the frontend single-page application."""
        index_file = STATIC_DIR / "index.html"
        return FileResponse(str(index_file))

    @app.post("/_pyview/upload/{session_id}/{widget_key}")
    async def upload_file(
        session_id: str,
        widget_key: str,
        file: UploadFile = File(...),
    ) -> dict[str, Any]:
        """Handle binary multipart file upload for file_uploader widget."""
        session = session_manager.get_or_create(session_id)
        content = await file.read()
        uploaded_obj = UploadedFile(
            name=file.filename or "uploaded_file",
            type=file.content_type or "application/octet-stream",
            size=len(content),
            data=content,
        )
        session.uploaded_files[widget_key] = uploaded_obj
        return {
            "status": "ok",
            "name": uploaded_obj.name,
            "type": uploaded_obj.type,
            "size": uploaded_obj.size,
        }

    @app.websocket("/_pyview/ws")
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """Handle persistent bidirectional WebSocket connection for a client session."""
        await websocket.accept()

        client_session_id = websocket.query_params.get("session_id")
        session_id = client_session_id or f"sess_{uuid.uuid4().hex[:12]}"
        session = session_manager.get_or_create(session_id)

        # Ingest initial query parameters from WebSocket URL
        for k, v in websocket.query_params.items():
            if k != "session_id":
                session.query_params[k] = v

        ws_lock = asyncio.Lock()

        async def send_payload(payload: dict[str, Any]) -> None:
            async with ws_lock:
                try:
                    await websocket.send_json(payload)
                except Exception:
                    pass

        current_run_task: asyncio.Task | None = None

        async def run_and_broadcast(
            active_triggers: set[str] | None = None,
            pending_values: dict[str, Any] | None = None,
        ) -> None:
            try:
                await send_payload({"type": "status", "status": "running"})
                result = await execute_session_run(
                    session=session,
                    runner=runner,
                    active_triggers=active_triggers,
                    pending_values=pending_values,
                )
                gen, elements, error = result
                page_config = result.page_config
                updated_query_params = result.query_params

                # If this run was superseded by a newer interaction, skip broadcasting
                if gen != session.current_generation:
                    return

                if error:
                    await send_payload({
                        "type": "error",
                        "generation": gen,
                        "error": error,
                    })
                else:
                    payload: dict[str, Any] = {
                        "type": "render",
                        "generation": gen,
                        "elements": elements,
                    }
                    if page_config is not None:
                        payload["page_config"] = page_config
                    if updated_query_params is not None:
                        payload["query_params"] = updated_query_params
                    await send_payload(payload)
                await send_payload({"type": "status", "status": "idle"})
            except asyncio.CancelledError:
                pass

        def schedule_run(
            active_triggers: set[str] | None = None,
            pending_values: dict[str, Any] | None = None,
        ) -> None:
            nonlocal current_run_task
            if pending_values:
                session.widget_values.update(pending_values)
            if current_run_task and not current_run_task.done():
                current_run_task.cancel()
            current_run_task = asyncio.create_task(
                run_and_broadcast(
                    active_triggers=active_triggers,
                    pending_values=pending_values,
                )
            )

        # Initial handshake and first run
        await send_payload({
            "type": "connected",
            "session_id": session_id,
        })
        schedule_run()

        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type")

                if msg_type in ("init", "rerun"):
                    if "query_params" in data and isinstance(data["query_params"], dict):
                        session.query_params.update(data["query_params"])
                    schedule_run()

                elif msg_type == "form_submit":
                    batch_values = data.get("values", {})
                    submit_key = data.get("submit_key") or data.get("key")

                    active_triggers: set[str] = set()
                    pending_values: dict[str, Any] = {}

                    if isinstance(batch_values, dict):
                        for k, v in batch_values.items():
                            pending_values[str(k)] = v

                    if submit_key:
                        str_submit = str(submit_key)
                        active_triggers.add(str_submit)
                        pending_values[str_submit] = True

                    schedule_run(
                        active_triggers=active_triggers,
                        pending_values=pending_values,
                    )

                elif msg_type in ("widget_event", "event"):
                    widget_key = data.get("key") or data.get("id")
                    val = data.get("value")
                    is_trigger = data.get("is_trigger", False)

                    active_triggers: set[str] = set()
                    pending_values: dict[str, Any] = {}

                    if widget_key:
                        str_key = str(widget_key)
                        pending_values[str_key] = val

                        # If trigger/button click or chat submit
                        if val is True or is_trigger:
                            active_triggers.add(str_key)

                    schedule_run(
                        active_triggers=active_triggers,
                        pending_values=pending_values,
                    )

        except WebSocketDisconnect:
            pass
        except Exception:
            pass
        finally:
            if current_run_task and not current_run_task.done():
                current_run_task.cancel()
            session.disconnected_at = time.time()

    return app
