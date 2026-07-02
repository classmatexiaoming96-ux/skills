#!/usr/bin/env python3
"""Kill a Codex tmux session.

Usage:
  python3 close.py                       # kill CODEX_SESSION (default)
  python3 close.py --session codex-abc   # kill a specific session
"""
import argparse
import os
import subprocess
import sys

SOCKET = os.environ.get("CODEX_SOCKET", "/tmp/codex-tmux")
SESSION = os.environ.get("CODEX_SESSION", "codex-main")


def main():
    parser = argparse.ArgumentParser(description="Kill a Codex tmux session")
    parser.add_argument("--session", default=SESSION, help=f"tmux session name (default: {SESSION})")
    parser.add_argument("--socket", default=SOCKET, help=f"tmux socket path (default: {SOCKET})")
    args = parser.parse_args()

    r = subprocess.run(
        ["tmux", "-S", args.socket, "kill-session", "-t", args.session],
        capture_output=True, text=True,
    )
    if r.returncode == 0:
        print(f"OK: {args.session} killed")
    else:
        print(f"Note: {r.stderr.strip() or 'session not found'}")
        sys.exit(1)


if __name__ == "__main__":
    main()
