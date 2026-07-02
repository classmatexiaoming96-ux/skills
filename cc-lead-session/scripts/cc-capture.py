#!/usr/bin/env python3
"""获取 Claude Code tmux session 的最近输出。

用法:
  python3 cc-capture.py --tmux-session my_session
  python3 cc-capture.py --tmux-session my_session --lines 200
  python3 cc-capture.py --tmux-session my_session --lines 0  # 全部 scrollback
"""

import argparse
import json
import os
import sys

from tmux_utils import capture_pane, check_alive

SOCKET_DEFAULT = os.path.join(os.path.expanduser("~"), ".tmux-sock", "socket")


def main():
    parser = argparse.ArgumentParser(description="获取 CC tmux session 的最近输出")
    parser.add_argument("--tmux-session", required=True, help="tmux session 名称")
    parser.add_argument("--lines", type=int, default=50,
                        help="捕获行数，0 表示全部 scrollback（上限受 tmux history-limit 限制，默认 2000）")
    parser.add_argument("--socket", required=False, default=None,
                        help="tmux socket 路径（可选，默认 ~/.tmux-sock/socket）")
    args = parser.parse_args()
    sock = args.socket or SOCKET_DEFAULT

    alive = check_alive(args.tmux_session, socket=sock)

    result = {
        "tmux_session": args.tmux_session,
        "tmux_alive": alive,
        "recent_output": None,
        "lines_captured": 0,
        "has_prompt": False,
    }

    if alive:
        output = capture_pane(args.tmux_session, lines=args.lines, socket=sock)
        lines = [l for l in output.splitlines() if l.strip()]
        result["recent_output"] = output
        result["lines_captured"] = len(lines)
        # CC 空闲时显示 ❯ 提示符
        result["has_prompt"] = any("❯" in l for l in output.splitlines()[-5:]) if lines else False

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
