---
name: cc-lead-session
description: Run a persistent Claude Code (CC) session inside tmux, send prompts, capture output, and clean up. Solves the orchestration problem of "CC is too long-running for my agent's single turn".
triggers:
  - "start claude code session"
  - "cc tmux"
  - "cc session"
  - "send prompt to claude code"
  - "claude code in tmux"
---

# Claude Code (CC) TMUX Session

Run a persistent Claude Code CLI session inside tmux, send prompts to it, and read back its output — useful when you need CC to do long-running autonomous work while your agent monitors and steers it.

## Why tmux?

Claude Code is an interactive TUI. If your agent spawns it directly, two problems appear:

1. **No persistence across agent turns** — when your agent's turn ends, the spawned CC process is killed.
2. **No stdout streaming** — CC's UI renders through alt-screen escape sequences that don't capture cleanly.

Wrapping CC in tmux solves both: tmux holds the TTY open across agent turns, and you can read the pane via `capture-pane` at any time.

## Quick Start

```bash
# 1. Spawn a CC session in a worktree
python3 scripts/cc-start.py \
  --worktree-path /path/to/your/worktree \
  --tmux-session cc-main \
  --prompt-file /tmp/task.md

# Output: {"tmux_session": "cc-main", "ready": true, "prompt_sent": true}

# 2. Send another prompt later (any time, from any agent turn)
python3 scripts/cc-send.py --tmux-session cc-main --prompt-file /tmp/follow-up.md

# 3. Read CC's recent output
python3 scripts/cc-capture.py --tmux-session cc-main --lines 200

# 4. Cleanup
python3 scripts/cc-close.py --tmux-session cc-main
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/cc-start.py` | Create a new CC tmux session and optionally send an initial prompt |
| `scripts/cc-send.py` | Send a prompt (from file) to an existing CC session |
| `scripts/cc-capture.py` | Capture pane output (JSON with aliveness flag) |
| `scripts/cc-close.py` | Kill a session |
| `scripts/tmux-utils.py` | Shared tmux helpers (capture_pane, send_keys, check_alive) |

All four scripts honor the `CC_SOCKET` env var. Default socket path is `$HOME/.tmux-sock/socket` — change it if your tmux server uses a different path.

## Architecture

```
tmux session (socket $CC_SOCKET)
  └── bash -c "cd <worktree> && claude"
        └── claude TUI (interactive prompt)
```

Unlike Codex, CC doesn't fork — it stays as a single foreground TUI process. So you don't need `script(1)` wrappers; `tmux new-session` is enough.

## CC Start in Detail

`cc-start.py` does four things:

1. Verifies the worktree path exists (exits non-zero if missing)
2. Creates a new tmux session running `cd <worktree> && claude`
3. Polls the pane until CC's prompt (`❯`) appears (15s timeout)
4. If `--prompt-file` is given, reads the file and sends it via `tmux send-keys`

Prints a JSON result like:
```json
{
  "tmux_session": "cc-main",
  "ready": true,
  "prompt_sent": true,
  "cc_remote_url": "https://claude.ai/code/session_..."
}
```

The `cc_remote_url` field is populated only when CC's `/remote-control` mode is active in the user's account. Public CC accounts won't have this — that's expected.

## Send Long Prompts Safely

Direct `tmux send-keys -l "$long_prompt"` over ~500 chars **loses characters** in some TTYs. The reliable pattern:

```bash
# Step 1: Write prompt to file
cat > /tmp/cc-task.md << 'EOF'
your full task prompt...
EOF

# Step 2: Send via script (uses tmux send-keys under the hood)
python3 scripts/cc-send.py --tmux-session cc-main --prompt-file /tmp/cc-task.md

# Step 3: Verify CC picked it up
sleep 5
python3 scripts/cc-capture.py --tmux-session cc-main --lines 20
# Should show CC processing the prompt (spinner, "Thinking...", etc.)
```

The bundled `cc-send.py` reads the prompt from a file (rather than a CLI arg) precisely to avoid character loss on long prompts.

## Read Output

```bash
# Last N lines (default 50)
python3 scripts/cc-capture.py --tmux-session cc-main

# Custom line count
python3 scripts/cc-capture.py --tmux-session cc-main --lines 500

# Full scrollback (0 = full)
python3 scripts/cc-capture.py --tmux-session cc-main --lines 0
```

`cc-capture.py` returns JSON with `recent_output`, `lines_captured`, `has_prompt` (true if CC is idle waiting for input), and `tmux_alive`. Parse the JSON in your agent to detect "CC is done, send next prompt" vs "CC is still working".

## Detect "CC Is Idle and Waiting"

CC's prompt shows `❯` when idle. Check it:

```bash
python3 scripts/cc-capture.py --tmux-session cc-main | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('alive:', d['tmux_alive'], '| idle:', d['has_prompt'])
"
```

`has_prompt=True` means CC is done with the previous turn and ready for the next prompt.

## Cleanup

```bash
# Just kill the tmux session
python3 scripts/cc-close.py --tmux-session cc-main

# Or use tmux directly
tmux -S $CC_SOCKET kill-session -t cc-main
```

Killing the tmux session also kills CC (since CC is the foreground process in the pane).

## Pitfalls

1. **Permission prompts block CC**: CC will pause and wait for human approval on certain actions (file edits, bash commands). In an unattended tmux session, this means **CC hangs forever**. Two fixes:
   - Start CC with `--permission-mode acceptEdits` to auto-approve file edits
   - Or send `2` (Yes, and don't ask again) via `tmux send-keys` when you see the approval prompt
   
   See `references/permission-loop.md` for the full pattern.

2. **CC's `❯` prompt detection is timing-sensitive**: CC shows `❯` while idle but also briefly while loading. Don't rely on a single poll — give it 5-10s before sending the next prompt.

3. **Long output scrolls off**: tmux's default `history-limit` is 2000 lines. For long-running CC tasks, set it higher:

   ```bash
   tmux -S $CC_SOCKET set-option -g history-limit 100000
   ```

   Add this to your `~/.tmux.conf` to make it permanent.

4. **CC exits on `Ctrl-C` or `Ctrl-D`**: if you accidentally send those via `tmux send-keys`, CC exits cleanly and the tmux pane shows a shell prompt. Check `tmux_alive` (the tmux session is still alive — only the CC process died).

5. **Worktree path with spaces**: wrap in quotes: `--worktree-path "/path/with spaces/repo"`. The bash invocation inside tmux is naive and won't escape correctly otherwise.

## Known Bugs

- CC's `/remote-control` URL extraction is regex-based (`https://claude.ai/code/session_...`). If Anthropic changes the URL format, `cc-capture.py` will silently return `cc_remote_url: null`.
- Some CC versions display the `❯` prompt in a different color/style than others; the literal-string check still works but might match transient UI states.

## End-to-End Verification

After installing this skill, run a quick smoke test:

```bash
# Use a throwaway test directory
mkdir -p /tmp/cc-smoke-test && cd /tmp/cc-smoke-test && git init

# Spawn
python3 scripts/cc-start.py \
  --worktree-path /tmp/cc-smoke-test \
  --tmux-session cc-smoke \
  --prompt-file <(echo "list files in this directory")

# Wait + read
sleep 10
python3 scripts/cc-capture.py --tmux-session cc-smoke --lines 30 | tail -20
# Expect: CC's response describing the directory

# Cleanup
python3 scripts/cc-close.py --tmux-session cc-smoke
```

If CC fails to start, check `tmux -S $CC_SOCKET list-sessions` and `pgrep -af claude` — leftovers from prior crashed sessions are the most common cause.
