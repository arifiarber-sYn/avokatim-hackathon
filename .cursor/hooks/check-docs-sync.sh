#!/usr/bin/env bash
# AgentStandard v1 — Cursor stop hook: nudge the agent if code changed but the
# docs/agents layer was not updated in the same working tree. Fails OPEN on
# any error — it never blocks.
#
# Rationale: AGENTS.md §2 requires a JOURNAL entry (+ STATE/DECISIONS/COMMS
# where relevant) after every change. This is the mechanical safety net for
# when that step is forgotten.
set -uo pipefail

CODE_PATTERN='^(backend|frontend)/.*\.(py|ts|tsx|js|jsx|css|sql)$'
DOCS_DIR='docs/agents/'

# Consume stdin (the hook receives JSON we don't need here).
cat >/dev/null 2>&1 || true

ROOT="${CURSOR_PROJECT_ROOT:-}"
if [ -z "$ROOT" ]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
fi
[ -z "$ROOT" ] && exit 0
cd "$ROOT" 2>/dev/null || exit 0

status="$(git status --porcelain 2>/dev/null || true)"
[ -z "$status" ] && exit 0   # clean tree → nothing to check

paths="$(printf '%s\n' "$status" | cut -c4-)"

code_changed="$(printf '%s\n' "$paths" | grep -E "$CODE_PATTERN" || true)"
docs_changed="$(printf '%s\n' "$paths" | grep -E "^${DOCS_DIR}|^AGENTS\.md$" || true)"

if [ -n "$code_changed" ] && [ -z "$docs_changed" ]; then
  msg="Code under backend/ or frontend/ has uncommitted changes, but docs/agents/ was not updated. Per AGENTS.md \\\"Session protocol\\\" and docs/agents/UPDATE-PROTOCOL.md: append a JOURNAL.md entry (never optional), update STATE.md if the live state changed, DECISIONS.md for architecture, COMMS.md for any outbound email change — before finishing."
  printf '{"followup_message":"%s"}\n' "$msg"
  exit 0
fi

# Commit nudge: docs updated but tree dirty → work is likely concluding.
if [ -n "$docs_changed" ]; then
  printf '{"followup_message":"The working tree still has uncommitted changes and docs/agents/ was updated — if the work is COMPLETE, commit it now (AGENTS.md §6: never leave finished work uncommitted, never push without request). If still in progress, ignore this."}\n'
fi
exit 0
