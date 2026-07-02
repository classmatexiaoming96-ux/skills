#!/usr/bin/env python3
"""tmux helpers for CC scripts."""

import os
import re
import subprocess
from typing import Optional


def capture_pane(session_name: str, lines: int = 50, socket: str = "") -> str:
    start = "-" if lines == 0 else f"-{lines}"
    argv = ["tmux"]
    if socket:
        argv.extend(["-S", socket])
    argv.extend(["capture-pane", "-t", session_name, "-p", "-S", start])
    r = subprocess.run(argv, capture_output=True, text=True, timeout=5)
    return r.stdout if r.returncode == 0 else ""


def extract_remote_url(output: str) -> Optional[str]:
    m = re.search(r"https://claude\.ai/code/session_\S+", output)
    return m.group(0) if m else None


def check_alive(session_name: str, socket: str = "") -> bool:
    argv = ["tmux"]
    if socket:
        argv.extend(["-S", socket])
    argv.extend(["has-session", "-t", session_name])
    try:
        r = subprocess.run(argv, capture_output=True, timeout=5)
        return r.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def send_keys(session_name: str, text: str, socket: str = "") -> None:
    argv = ["tmux"]
    if socket:
        argv.extend(["-S", socket])
    argv.extend(["send-keys", "-t", session_name, "-l", text])
    subprocess.run(argv, check=True, capture_output=True, timeout=10)

    argv2 = ["tmux"]
    if socket:
        argv2.extend(["-S", socket])
    argv2.extend(["send-keys", "-t", session_name, "Enter"])
    subprocess.run(argv2, check=True, capture_output=True, timeout=10)
