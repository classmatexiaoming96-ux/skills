---
name: codex-tmux-session-v2
description: Manage persistent Codex CLI sessions in tmux — spawn, send, recv, close. Solves Codex fork/exit problem.
triggers:
  - "start codex session"
  - "codex tmux"
  - "codex persistent"
  - "codex session"
  - "send prompt to codex"
---

# Codex TMUX Session

Run a persistent OpenAI Codex CLI session inside tmux, send prompts to it, and read back its output — useful when you need Codex to do long-running autonomous work while your agent monitors and steers it.

## The Fork Problem

Codex TUI mode forks immediately:

- **Parent** (exits): TUI rendering
- **Child** (stays): `app-server` + MCP

If you do `tmux new-session "codex"`, the parent exits, tmux kills the pane, and the session dies within seconds.

**Solution**: wrap with `script(1)` to keep the PTY alive after the parent exits:

```bash
tmux new-session -d -s codex-main 'script -q -c codex /dev/null'
```

The `script` process holds the PTY open. Codex's `app-server` (the long-running child) attaches to the same PTY and keeps responding to prompts.

**Process tree (correct)**:
```
tmux server
  └── tmux new-session
        └── script (holds TTY)
              └── codex app-server (long-running)
```

**Verify**:
```bash
ps -o pid,ppid,cmd --ppid <script_pid>
# Should show codex as child of script
```

## Architecture

```
tmux session (socket $CODEX_SOCKET)
  └── script (keeps TTY alive)
        └── codex (child app-server holds PTY)
```

## Quick Start

```bash
# 1. Spawn
python3 scripts/spawn.py
# Output: SOCKET=/tmp/tmux-codex  SESSION=codex-XXXXXXXX

# 2. Send a prompt
python3 scripts/send.py --session codex-XXXXXXXX --prompt "Refactor the auth module"

# 3. Read output
python3 scripts/recv.py --session codex-XXXXXXXX --limit 200

# 4. Close
python3 scripts/close.py --session codex-XXXXXXXX
```

Or call the bundled scripts with custom socket/session via env vars:

```bash
export CODEX_SOCKET=/tmp/tmux-codex
export CODEX_SESSION=codex-main
python3 scripts/send.py --prompt "..."
python3 scripts/recv.py --limit 200
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/spawn.py` | Create a new Codex tmux session (uuid-suffixed name) |
| `scripts/send.py` | Send a prompt to a session |
| `scripts/recv.py` | Capture pane output (full scrollback with `--full`) |
| `scripts/close.py` | Kill a session |

All four scripts honor `CODEX_SOCKET` and `CODEX_SESSION` env vars (default: `/tmp/tmux-codex` and `codex-main`).

## Spawn in Detail

`spawn.py` does five things:

1. Creates the socket directory with `0700` perms (tmux refuses world-writable socket dirs)
2. Kills any pre-existing session with the same name (idempotent)
3. Runs `tmux new-session -d -s NAME 'script -q -c codex /dev/null'`
4. Sets `history-limit 100000` so long task outputs survive
5. Polls the pane until `OpenAI Codex` or a model-name string appears (30s timeout)

Prints `OK: session NAME alive` plus `SOCKET=...` and `SESSION=...` on success. Non-zero exit + last 500 chars of pane output on failure.

## Send Long Prompts Safely

Direct `tmux send-keys -l "$long_prompt"` over ~500 chars **loses characters** in some TTYs. The reliable pattern:

```bash
# Step 1: Write prompt to file
cat > /tmp/codex-task.md << 'EOF'
your full task prompt...
EOF

# Step 2: Read and send via script (uses send-keys in chunks internally)
prompt="$(cat /tmp/codex-task.md)"
python3 scripts/send.py --prompt "$prompt"

# Step 3: Verify Codex picked it up
sleep 5
python3 scripts/recv.py --limit 8 | tail -8
# Should show "❋ Thinking..." or similar
```

The bundled `send.py` already handles chunking for long prompts.

## Read Output

```bash
# Last N lines (default 500)
python3 scripts/recv.py --limit 200

# Full scrollback (slow on very long sessions)
python3 scripts/recv.py --full
```

Output is the raw pane text — grep/parse with your own tooling.

## Pitfalls

1. **PROXY REQUIRED FOR TUI MODE** (most common failure): Codex TUI hits `chatgpt.com/backend-api/wham/apps` for the `codex_apps` MCP server at startup. Without a proxy, the connection hangs in `⚠ Reconnecting N/5` and Codex never enters the prompt screen — every `send-keys` gets echoed but produces no response. Set `HTTPS_PROXY` / `HTTP_PROXY` (or use a proxy wrapper script) before spawning.

2. **World-writable socket dir**: tmux refuses to use a socket dir with `o+w`. Always `chmod 0700` before `tmux new-session -S`.

3. **Stale `codex` processes**: if a previous Codex session crashed, killing the tmux session may leave a `codex app-server` orphan. Check with `pgrep -af codex` and `kill` leftovers before respawning.

4. **Long prompt chunking**: `tmux send-keys -l` over ~500 chars can drop chars on some terminals. The bundled `send.py` handles this; if you call `tmux` directly, use a chunked approach.

5. **Output capture misses past scrollback**: by default, capture-pane only shows the visible viewport. Use `capture-pane -p -S -` to get the full scrollback (what `recv.py --full` does).

## Known Bugs

This skill is exercised against Codex CLI's `codex app-server` mode. Known failure modes:

- Codex uses one OpenAI account quota. Running 2+ concurrent Codex sessions on the same account will cause one to hit `usage limit` while the other works.
- Some Codex versions fork differently — if the `script` wrapper trick stops working, check `ps -o pid,ppid,cmd --ppid <script_pid>` and confirm `codex` is still a child of `script`.

## End-to-End Verification

After installing this skill, run a quick smoke test:

```bash
# Spawn
OUT=$(python3 scripts/spawn.py)
SESSION=$(echo "$OUT" | grep SESSION= | cut -d= -f2)
echo "Spawned: $SESSION"

# Send a trivial prompt
python3 scripts/send.py --session "$SESSION" --prompt "echo hello"

# Wait for Codex to respond
sleep 10
python3 scripts/recv.py --session "$SESSION" --limit 30 | tail -20
# Expect: codex prints "hello" and waits for next prompt

# Cleanup
python3 scripts/close.py --session "$SESSION"
```

If spawn times out, check `pgrep -af tmux` and `pgrep -af codex` — leftovers from prior crashed sessions are the most common cause.
