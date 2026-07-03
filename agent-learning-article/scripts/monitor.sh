#!/bin/bash
# Monitor script for Agent Learning Codex article translation
# Usage: edit SESSION/ARTIFACT/SENTINEL then run
# Returns: 0=done, 1=session died, 3=usage limit, 2=timeout

SOCKET=/tmp/tmux-codex
SESSION=codex-pN-slug          # ← EDIT per run
ARTIFACT=/tmp/usersite/agent_learning/articles/slug.html  # ← EDIT per run
SENTINEL="DONE slug"           # ← EDIT per run
MAX_CYCLES=120                 # 120 * 30s = 60 min

exec >> /tmp/monitor-{SESSION}.log 2>&1
echo "[$(date '+%H:%M:%S')] watcher started: $SESSION"

for i in $(seq 1 $MAX_CYCLES); do
  sleep 30

  if ! tmux -S "$SOCKET" list-sessions 2>/dev/null | grep -q "$SESSION"; then
    echo "[$(date '+%H:%M:%S')] session died"; exit 1
  fi

  PANE=$(tmux -S "$SOCKET" capture-pane -t "$SESSION" -p -S -100 2>/dev/null)

  # Strict sentinel: standalone line OR • bullet
  if echo "$PANE" | grep -qE "^[[:space:]]*$SENTINEL[[:space:]]*$" || \
     echo "$PANE" | grep -qE '•[[:space:]]+'"$SENTINEL"'[[:space:]]*$'; then
    if [ -f "$ARTIFACT" ] && [ -s "$ARTIFACT" ]; then
      echo "[$(date '+%H:%M:%S')] ✓ sentinel + artifact OK"
      cd /tmp/usersite 2>/dev/null && git log -2 --oneline
      exit 0
    else
      echo "[$(date '+%H:%M:%S')] ⚠ sentinel matched but artifact missing/empty"
    fi
  fi

  # Auto-approve sandbox
  if echo "$PANE" | grep -qE "(Yes, proceed|Yes, and don't ask again)"; then
    tmux -S "$SOCKET" send-keys -t "$SESSION" Enter 2>/dev/null
    echo "[$(date '+%H:%M:%S')] [approve] sandbox"
  fi

  # Detect usage limit
  if echo "$PANE" | grep -qE "(usage limit|try again at)"; then
    echo "[$(date '+%H:%M:%S')] ⚠ usage limit hit"; exit 3
  fi

  WORKING=$(echo "$PANE" | grep -oE "Working \([0-9]+m [0-9]+s" | tail -1)
  [ -n "$WORKING" ] && echo "[$(date '+%H:%M:%S')] cycle $i ($WORKING)"
done

echo "[$(date '+%H:%M:%S')] ✗ TIMEOUT"; exit 2
