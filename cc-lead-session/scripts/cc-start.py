#!/usr/bin/env python3
"""Lightweight CC tmux session starter.

Usage:
  python3 cc-start.py --worktree-path /path/to/repo --tmux-session cc-main \
                      [--prompt-file /tmp/task.md] [--socket /tmp/tmux-cc]

Exits 0 on success and prints JSON:
  {"tmux_session": "cc-main", "ready": true, "prompt_sent": true}
"""
import argparse
import json
import os
import subprocess
import sys
import time

from tmux_utils import capture_pane, extract_remote_url, send_keys, check_alive

SOCKET_DEFAULT = os.path.join(os.path.expanduser("~"), ".tmux-sock", "socket")
STARTUP_WAIT = 5
MAX_STARTUP_WAIT = 20


def shlex_quote(path: str) -> str:
    if " " in path or "\t" in path:
        return "'" + path.replace("'", "'\''") + "'"
    return path


def start_tmux_session(session_name: str, worktree_path: str, socket: str) -> None:
    if not os.path.isdir(worktree_path):
        raise FileNotFoundError(f"worktree path does not exist: {worktree_path}")
    sock_dir = os.path.dirname(socket) or "."
    os.makedirs(sock_dir, exist_ok=True)
    try:
        os.chmod(sock_dir, 0o700)
    except PermissionError:
        pass
    cmd = f"cd {shlex_quote(worktree_path)} && claude"
    tmux_cmd = ["tmux", "-S", socket, "new-session", "-d", "-s", session_name, cmd]
    subprocess.run(tmux_cmd, check=True, capture_output=True)


def wait_for_ready(session_name: str, socket: str) -> dict:
    time.sleep(STARTUP_WAIT)
    deadline = time.time() + (MAX_STARTUP_WAIT - STARTUP_WAIT)
    while time.time() < deadline:
        output = capture_pane(session_name, lines=30, socket=socket)
        if not output:
            time.sleep(1)
            continue
        if "❯" in output:
            url = extract_remote_url(output)
            return {"ready": True, "cc_remote_url": url}
        time.sleep(1)
    return {"ready": False, "timeout": True}


def send_prompt_from_file(session_name: str, prompt_file: str, socket: str) -> bool:
    with open(prompt_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        return False
    send_keys(session_name, content, socket=socket)
    return True


def main():
    parser = argparse.ArgumentParser(description="Start a Claude Code tmux session")
    parser.add_argument("--worktree-path", required=True, help="Working directory for CC")
    parser.add_argument("--tmux-session", required=True, help="tmux session name")
    parser.add_argument("--prompt-file", help="Optional: send this file's contents as the first prompt")
    parser.add_argument("--socket", default=SOCKET_DEFAULT, help=f"tmux socket path (default: {SOCKET_DEFAULT})")
    args = parser.parse_args()

    result = {"tmux_session": args.tmux_session}
    try:
        start_tmux_session(args.tmux_session, args.worktree_path, args.socket)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        result["error"] = str(e)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    ready_info = wait_for_ready(args.tmux_session, args.socket)
    result.update(ready_info)

    if args.prompt_file:
        try:
            result["prompt_sent"] = send_prompt_from_file(
                args.tmux_session, args.prompt_file, args.socket
            )
        except Exception as e:
            result["prompt_sent"] = False
            result["prompt_error"] = str(e)
    else:
        result["prompt_sent"] = False

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
