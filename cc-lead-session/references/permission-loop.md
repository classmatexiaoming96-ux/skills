# CC Permission Approval Loop

When CC runs unattended in tmux, permission prompts block forever because there's no human to approve them. This is the most common reason "CC hangs in tmux".

## The Two Modes

| Flag | Effect | When to Use |
|------|--------|-------------|
| (no flag) | CC pauses for human approval on every edit | Interactive TUI use |
| `--permission-mode acceptEdits` | Auto-approve file edits; still prompt for bash | Mixed interactive + automated |
| `--dangerously-skip-permissions` | Auto-approve everything | **Root user is BLOCKED from this flag** |

## Recommended Pattern

Start CC with `--permission-mode acceptEdits`:

```python
cmd = f"cd {worktree_path} && claude --permission-mode acceptEdits"
```

This auto-approves file edits (the most common approval prompt) while still asking for bash command approval.

## Auto-Approving Bash Prompts via tmux

When CC shows:
```
Do you want to proceed?
1. Yes
2. Yes, and don't ask again for this command
3. No
```

Send `2` (Yes, don't ask again) to batch-approve:

```bash
tmux -S $CC_SOCKET send-keys -t cc-main "2" Enter
```

Build a polling loop in your agent:

```python
import time, json, subprocess

while True:
    r = subprocess.run(
        ["python3", "scripts/cc-capture.py", "--tmux-session", "cc-main"],
        capture_output=True, text=True,
    )
    state = json.loads(r.stdout)
    output = state.get("recent_output", "")
    if "Do you want to proceed?" in output and "1. Yes" in output:
        subprocess.run(
            ["tmux", "-S", socket, "send-keys", "-t", "cc-main", "2", "Enter"],
            check=True,
        )
        time.sleep(2)
    elif state.get("has_prompt"):
        break  # CC is idle, ready for next prompt
    time.sleep(5)
```

## Pitfalls

1. **The "shift+tab" UI doesn't work via tmux send-keys**: CC's `accept edits on (shift+tab to cycle) · esc to interrupt` menu is interactive — number keys don't navigate it. Send Enter (which confirms the highlighted option) and then approve the next bash prompt with `2`.

2. **Multiple permission prompts in a row**: a single complex task can trigger 5-10 prompts. Use `2` (don't ask again) to avoid round-trips.

3. **`--dangerously-skip-permissions` blocked on root**: if `whoami` returns `root`, Claude Code refuses this flag. Use `--permission-mode acceptEdits` instead.
