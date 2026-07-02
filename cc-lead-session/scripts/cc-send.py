#!/usr/bin/env python3
"""向已有的 CC tmux session 发送 prompt，不启动新 CC。"""
import argparse
import os
from tmux_utils import capture_pane, extract_remote_url, send_keys, check_alive

SOCKET_DEFAULT = os.path.join(os.path.expanduser("~"), ".tmux-sock", "socket")

def send_prompt(session_name: str, prompt_file: str, socket: str = None):
    with open(prompt_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
    send_keys(session_name, content, socket=socket or SOCKET_DEFAULT)

def main():
    parser = argparse.ArgumentParser(description="向已有 CC tmux session 发送 prompt")
    parser.add_argument("--tmux-session", required=True, help="tmux session 名称")
    parser.add_argument("--prompt-file", required=True, help="Prompt 文件路径")
    parser.add_argument("--socket", required=False, default=None, help="tmux socket 路径（可选，默认使用 ~/.tmux-sock/socket）")
    args = parser.parse_args()
    send_prompt(args.tmux_session, args.prompt_file, socket=args.socket)
    print(f"Prompt sent to {args.tmux_session}")

if __name__ == "__main__":
    main()
