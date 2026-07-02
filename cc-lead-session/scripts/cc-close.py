#!/usr/bin/env python3
"""Kill a CC tmux session.

Usage:
  python3 cc-close.py --tmux-session cc-main [--socket /tmp/tmux-cc]
"""
import argparse
import os
import subprocess
import sys

SOCKET_DEFAULT = os.path.join(os.path.expanduser("~"), ".tmux-sock", "socket")


def main():
    parser = argparse.ArgumentParser(description="Kill a CC tmux session")
    parser.add_argument("--tmux-session", required=True, help="tmux session name")
    parser.add_argument("--socket", default=SOCKET_DEFAULT, help=f"tmux socket path (default: {SOCKET_DEFAULT})")
    args = parser.parse_args()

    r = subprocess.run(
        ["tmux", "-S", args.socket, "kill-session", "-t", args.tmux_session],
        capture_output=True, text=True,
    )
    if r.returncode == 0:
        print(f"OK: {args.tmux_session} killed")
    else:
        print(f"Note: {r.stderr.strip() or 'session not found'}")
        sys.exit(1)


if __name__ == "__main__":
    main()
