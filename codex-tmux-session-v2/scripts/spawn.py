#!/usr/bin/env python3
"""Spawn Codex in tmux session using script wrapper to survive fork.

Usage:
  python3 spawn.py                          # uses $CODEX_SOCKET or /tmp/codex-tmux
  CODEX_SOCKET=/tmp/my-socket python3 spawn.py
"""
import os
import subprocess
import sys
import time
import uuid

DEFAULT_SOCKET = "/tmp/codex-tmux/socket"


def resolve_socket_dir():
    """Resolve socket parent dir.

    Priority:
      1. $CODEX_SOCKET env var (full socket file path, use its dirname)
      2. $CODEX_SOCKET_DIR env var (explicit parent dir)
      3. Default /tmp/codex-tmux
    """
    explicit = os.environ.get("CODEX_SOCKET")
    if explicit:
        return os.path.dirname(explicit) or "."
    return os.environ.get("CODEX_SOCKET_DIR", os.path.dirname(DEFAULT_SOCKET))


def run(argv, check=True, capture=True):
    r = subprocess.run(argv, capture_output=capture, text=True)
    if r.returncode != 0 and check:
        print("FAIL: {}".format(argv), file=sys.stderr)
        print(r.stderr, file=sys.stderr)
        sys.exit(1)
    return r


def get_socket():
    """Get socket path, creating the dir with 0700 perms."""
    socket_dir = resolve_socket_dir()
    os.makedirs(socket_dir, mode=0o700, exist_ok=True)
    return os.path.join(socket_dir, "socket")


def wait_until_ready(socket, session, timeout=30):
    """Poll pane until it shows Codex ready pattern or times out."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = run(["tmux", "-S", socket, "list-panes", "-t", session, "-F", "#{pane_dead}"], check=False)
        if r.stdout.strip() == "0":
            r2 = run(["tmux", "-S", socket, "capture-pane", "-t", session, "-p"], check=False)
            if "OpenAI Codex" in r2.stdout or "gpt-" in r2.stdout:
                return True
        time.sleep(0.5)
    return False


def main():
    socket = get_socket()
    session = "codex-{}".format(uuid.uuid4().hex[:8])

    run(["tmux", "-S", socket, "kill-session", "-t", session], check=False)
    time.sleep(0.3)

    os.chmod(os.path.dirname(socket), 0o700)

    run([
        "tmux", "-S", socket, "new-session", "-d", "-s", session,
        "script", "-q", "-c", "codex", "/dev/null"
    ])

    run(["tmux", "-S", socket, "set-option", "-g", "history-limit", "100000"])

    if not wait_until_ready(socket, session):
        print("FAIL: session {} did not become ready".format(session), file=sys.stderr)
        r = run(["tmux", "-S", socket, "capture-pane", "-t", session, "-p"], check=False)
        print("Pane output:\n" + r.stdout[:500])
        sys.exit(1)

    print("OK: session {} alive".format(session))
    print("SOCKET={}".format(socket))
    print("SESSION={}".format(session))


if __name__ == "__main__":
    main()
