"""Command-line interface for PyView.

Usage:
    pyview run app.py [--host 127.0.0.1] [--port 8501]
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import uvicorn

import pyview
from pyview.server import create_app


def main() -> None:
    """CLI entry point for PyView."""
    parser = argparse.ArgumentParser(
        prog="pyview",
        description="PyView: Lightweight, pure-Python reactive web framework.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pyview {pyview.__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # `pyview run <script>`
    run_parser = subparsers.add_parser("run", help="Run a PyView Python script")
    run_parser.add_argument(
        "script",
        type=str,
        help="Path to the Python application script (e.g. app.py)",
    )
    run_parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host interface to bind to (default: 127.0.0.1)",
    )
    run_parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port to run the web server on (default: 8501)",
    )
    run_parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Logging level (default: info)",
    )

    args = parser.parse_args()

    if args.command == "run":
        script_file = Path(args.script).resolve()
        if not script_file.exists():
            print(f"Error: Script file not found: {args.script}", file=sys.stderr)
            sys.exit(1)

        print("=" * 60)
        print(f"  🚀 PyView v{pyview.__version__}")
        print(f"  📄 App:  {script_file}")
        print(f"  🌐 URL:  http://{args.host}:{args.port}")
        print("=" * 60)

        app = create_app(script_file)
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level=args.log_level,
        )
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
