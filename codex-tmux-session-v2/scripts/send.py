#!/usr/bin/env python3
"""Send a prompt to Codex via tmux send-keys.

Usage:
  python3 send.py --prompt "your prompt here"
  python3 send.py --prompt-file /tmp/task.md
  python3 send.py --prompt "multi-line\nworks too"
"""
import argparse
import os
import subprocess
import sys

SOCKET = os.environ.get("CODEX_SOCKET", "/tmp/codex-tmux")
SESSION = os.environ.get("CODEX_SESSION", "codex-main")


def send(prompt: str, session: str = None, socket: str = None) -> bool:
    sess = session or SESSION
    sock = socket or SOCKET

    argv = ["tmux", "-S", sock, "send-keys", "-t", sess, "-l", prompt]
    r = subprocess.run(argv, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"SEND FAIL: {r.stderr.strip()}", file=sys.stderr)
        return False

    r2 = subprocess.run(
        ["tmux", "-S", sock, "send-keys", "-t", sess, "Enter"],
        capture_output=True, text=True,
    )
    if r2.returncode != 0:
        print(f"SEND Enter FAIL: {r2.stderr.strip()}", file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Send a prompt to a Codex tmux session")
    parser.add_argument("--prompt", help="Prompt text (use \\n for newlines)")
    parser.add_argument("--prompt-file", help="Read prompt from this file")
    parser.add_argument("--session", default=SESSION, help=f"tmux session name (default: {SESSION})")
    parser.add_argument("--socket", default=SOCKET, help=f"tmux socket path (default: {SOCKET})")
    args = parser.parse_args()

    if args.prompt:
        prompt = args.prompt.replace("\\n", "\n")
    elif args.prompt_file:
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
    else:
        prompt = "hello"
        print(f"Warning: no --prompt or --prompt-file given, using 'hello'", file=sys.stderr)

    if send(prompt, session=args.session, socket=args.socket):
        print(f"OK: prompt sent to {args.session}")


if __name__ == "__main__":
    main()
