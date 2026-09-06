"""Execution flow control primitives (rerun and stop) for PyView."""

from __future__ import annotations


class StopException(BaseException):
    """Raised by pv.stop() to gracefully cease script execution."""
    pass


class RerunException(BaseException):
    """Raised by pv.rerun() to immediately interrupt and re-execute the script."""
    pass


class CancelledException(BaseException):
    """Raised when a script rerun is superseded/cancelled by a newer interaction."""
    pass


def stop() -> None:
    """Halt script execution immediately.

    PyView will not execute any remaining statements in the script for this rerun.
    All elements registered before `pv.stop()` was called are preserved and rendered to the client.
    """
    raise StopException()


def rerun() -> None:
    """Interrupt the current run and trigger an immediate top-to-bottom re-execution of the script."""
    raise RerunException()
