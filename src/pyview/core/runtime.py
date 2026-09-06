"""Runtime engine, session management, and script execution for PyView.

Handles top-to-bottom script execution in isolated worker threads,
state persistence, generation tracking for stale run cancellation,
and clean exception handling.
"""

from __future__ import annotations

import asyncio
from contextvars import copy_context
from dataclasses import dataclass, field
import os
from pathlib import Path
import threading
import time
import traceback
from types import CodeType
from typing import Any

from pyview.core.context import ExecutionContext, reset_current_context, set_current_context
from pyview.core.flow import CancelledException, RerunException, StopException
from pyview.core.state import SessionState


class RunResult(tuple):
    """Result tuple (generation, elements, error) with extra attributes for page_config and query_params."""

    page_config: Any
    query_params: dict[str, Any] | None

    def __new__(
        cls,
        generation: int,
        elements: list[dict[str, Any]],
        error: str | None,
        page_config: Any = None,
        query_params: dict[str, Any] | None = None,
    ) -> RunResult:
        instance = super().__new__(cls, (generation, elements, error))
        instance.page_config = page_config
        instance.query_params = query_params
        return instance

    @property
    def generation(self) -> int:
        return self[0]

    @property
    def elements(self) -> list[dict[str, Any]]:
        return self[1]

    @property
    def error(self) -> str | None:
        return self[2]


@dataclass
class Session:
    """Represents an isolated user browser session."""

    session_id: str
    session_state: SessionState = field(default_factory=SessionState)
    widget_values: dict[str, Any] = field(default_factory=dict)
    uploaded_files: dict[str, Any] = field(default_factory=dict)
    query_params: dict[str, Any] = field(default_factory=dict)
    current_generation: int = 0
    created_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
    disconnected_at: float | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)
    active_context: ExecutionContext | None = None

    def next_generation(self) -> int:
        """Atomically increment and return the next generation number."""
        with self._lock:
            self.current_generation += 1
            self.last_active_at = time.time()
            if self.active_context is not None:
                # Mark previous running context as cancelled
                self.active_context.is_cancelled = True
            return self.current_generation

    def cancel(self) -> None:
        """Cancel any running execution context for this session."""
        with self._lock:
            if self.active_context is not None:
                self.active_context.is_cancelled = True


class ScriptRunner:
    """Compiles and executes user application scripts."""

    def __init__(self, script_path: str | Path) -> None:
        self.script_path = Path(script_path).resolve()
        if not self.script_path.exists():
            raise FileNotFoundError(f"PyView script not found: {self.script_path}")
        self._compiled_code: CodeType | None = None
        self._last_mtime: float = 0.0
        self._lock = threading.Lock()

    def _get_code(self) -> CodeType:
        """Load and compile the script bytecode, recompiling if the source changed."""
        mtime = os.path.getmtime(self.script_path)
        with self._lock:
            if self._compiled_code is None or mtime > self._last_mtime:
                source = self.script_path.read_text(encoding="utf-8")
                self._compiled_code = compile(
                    source,
                    str(self.script_path),
                    "exec",
                    dont_inherit=True,
                )
                self._last_mtime = mtime
            return self._compiled_code

    def run_in_context(
        self, ctx: ExecutionContext
    ) -> tuple[list[dict[str, Any]], str | None, Any, dict[str, Any] | None]:
        """Execute the user script synchronously within the provided ExecutionContext.

        Returns (elements, error_or_rerun_signal, page_config, updated_query_params).
        """
        token = set_current_context(ctx)
        try:
            if ctx.is_cancelled:
                return [], None, None, None

            code = self._get_code()
            script_globals: dict[str, Any] = {
                "__name__": "__main__",
                "__file__": str(self.script_path),
                "__doc__": None,
                "__builtins__": __builtins__,
            }

            # Execute top-to-bottom
            exec(code, script_globals)

            if ctx.is_cancelled:
                return [], None, None, None

            q_params = dict(ctx.session.query_params) if ctx.query_params_mutated else None
            p_config = ctx.page_config.to_dict() if ctx.page_config else None
            return ctx.get_serialized_elements(), None, p_config, q_params
        except StopException:
            # Graceful stop via pv.stop()
            if ctx.is_cancelled:
                return [], None, None, None
            q_params = dict(ctx.session.query_params) if ctx.query_params_mutated else None
            p_config = ctx.page_config.to_dict() if ctx.page_config else None
            return ctx.get_serialized_elements(), None, p_config, q_params
        except CancelledException:
            # Stale execution interrupted immediately by newer user interaction
            return [], None, None, None
        except RerunException:
            # Immediate rerun request via pv.rerun()
            return [], "__RERUN__", None, None
        except Exception:
            if ctx.is_cancelled:
                return [], None, None, None
            tb = traceback.format_exc()
            p_config = ctx.page_config.to_dict() if ctx.page_config else None
            return ctx.get_serialized_elements(), tb, p_config, None
        finally:
            reset_current_context(token)


class SessionManager:
    """Registry and lifecycle manager for all active sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def _cleanup_stale_sessions_locked(self, max_idle_seconds: float) -> int:
        now = time.time()
        removed = 0
        for sid, sess in list(self._sessions.items()):
            disc = getattr(sess, "disconnected_at", None)
            last_act = getattr(sess, "last_active_at", sess.created_at)
            if disc is not None and (now - disc) > max_idle_seconds:
                del self._sessions[sid]
                removed += 1
            elif (now - last_act) > (max_idle_seconds * 2):
                del self._sessions[sid]
                removed += 1
        return removed

    def cleanup_stale_sessions(self, max_idle_seconds: float = 1800.0) -> int:
        """Remove disconnected or idle sessions to prevent memory leaks."""
        with self._lock:
            return self._cleanup_stale_sessions_locked(max_idle_seconds)

    def get_or_create(self, session_id: str) -> Session:
        with self._lock:
            if session_id not in self._sessions:
                if len(self._sessions) >= 30:
                    self._cleanup_stale_sessions_locked(1800.0)
                self._sessions[session_id] = Session(session_id=session_id)
            sess = self._sessions[session_id]
            sess.last_active_at = time.time()
            sess.disconnected_at = None
            return sess

    def remove(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def list_sessions(self) -> list[Session]:
        with self._lock:
            return list(self._sessions.values())


async def execute_session_run(
    session: Session,
    runner: ScriptRunner,
    active_triggers: set[str] | None = None,
    pending_values: dict[str, Any] | None = None,
) -> RunResult:
    """Asynchronously schedule a script execution on a worker thread.

    Returns a 3-tuple `RunResult(generation, elements, error)` with `.page_config` and `.query_params` attributes.
    """
    while True:
        gen = session.next_generation()
        ctx = ExecutionContext(
            session=session,
            generation=gen,
            active_triggers=active_triggers or set(),
            pending_values=pending_values or {},
        )
        session.active_context = ctx

        loop = asyncio.get_running_loop()

        # Run in thread pool without blocking FastAPI's async event loop
        elements, error_signal, page_config, query_params = await loop.run_in_executor(
            None,
            copy_context().run,
            runner.run_in_context,
            ctx,
        )

        # Check if rerun requested via pv.rerun()
        if error_signal == "__RERUN__":
            # Loop around and execute fresh generation
            active_triggers = set()
            pending_values = {}
            continue

        # Check if this run is still the latest generation
        is_latest = (gen == session.current_generation and not ctx.is_cancelled)
        if not is_latest:
            return RunResult(gen, [], None, None, None)

        return RunResult(gen, elements, error_signal, page_config, query_params)
