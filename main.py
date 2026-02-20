from __future__ import annotations

import argparse
import sys


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Search Agent")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in terminal mode instead of launching the desktop app window.",
    )
    parser.add_argument("query", nargs="*", help="Optional CLI query text.")
    return parser.parse_args(argv)


def _check_tkinter() -> bool:
    try:
        import tkinter  # noqa: F401
    except Exception as error:
        print("Tkinter is not available in this Python environment.")
        print(f"Details: {error}")
        if sys.platform == "darwin":
            print("On macOS, install a Python build that includes Tk support (for example python.org installers).")
        else:
            print("Install Tk support for your Python runtime (for example: python3-tk on Linux).")
        return False
    return True


def _run_cli(query_parts: list[str]) -> int:
    from ui_agent import run_agent

    query = " ".join(query_parts).strip()
    if not query:
        try:
            query = input("Enter a topic to research: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return 130

    if not query:
        print("Please provide a query.")
        return 2

    try:
        answer = run_agent(query)
    except Exception as error:
        print(f"Error: {error}")
        return 1

    print(answer)
    return 0


def _run_gui() -> int:
    if not _check_tkinter():
        return 1

    from ui_app import launch_gui

    return launch_gui()


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if args.cli:
        return _run_cli(args.query)
    return _run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
