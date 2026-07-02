#!/usr/bin/env python3
"""Capture Codex pane output.

Usage:
  python3 recv.py                          # last 500 lines
  python3 recv.py --limit 200              # last 200 lines
  python3 recv.py --full                   # full scrollback
  python3 recv.py --session codex-abc      # different session
"""
import argparse
import os
import subprocess
import sys

SOCKET = os.environ.get("CODEX_SOCKET", "/tmp/codex-tmux")
SESSION = os.environ.get("CODEX_SESSION", "codex-main")


def main():
    parser = argparse.ArgumentParser(description="Capture Codex pane output")
    parser.add_argument("--limit", type=int, default=500, help="Last N lines (default 500)")
    parser.add_argument("--full", action="store_true", help="Capture full scrollback (overrides --limit)")
    parser.add_argument("--session", default=SESSION, help=f"tmux session name (default: {SESSION})")
    parser.add_argument("--socket", default=SOCKET, help=f"tmux socket path (default: {SOCKET})")
    args = parser.parse_args()

    if args.full:
        start = "-"
    else:
        start = f"-{args.limit}"

    argv = ["tmux", "-S", args.socket, "capture-pane", "-t", args.session, "-p", "-S", start]
    r = subprocess.run(argv, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"RECV FAIL: {r.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    print(r.stdout, end="")


if __name__ == "__main__":
    main()
