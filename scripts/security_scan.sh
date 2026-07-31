#!/usr/bin/env bash
# Weekly dependency scan (D-033): pip-audit (backend) + npm audit (frontend).
# The summary goes to the platform operator via Halim (Telegram); full output
# is kept in data/security-scan.log. Wired to avokatim-secscan.timer.
set -u
cd "$(dirname "$0")/.."

LOG=data/security-scan.log
{
  echo "===== security scan $(date -Iseconds) ====="

  echo "--- pip-audit (backend) ---"
  PIP_REPORT=$(backend/.venv/bin/pip-audit --skip-editable 2>&1)
  PIP_STATUS=$?
  echo "$PIP_REPORT"

  echo "--- npm audit (frontend) ---"
  NPM_REPORT=$(cd frontend && npm audit --omit=dev 2>&1)
  NPM_STATUS=$?
  echo "$NPM_REPORT"
} >> "$LOG"

# Short human summary for the Telegram report
PIP_SUMMARY=$(echo "$PIP_REPORT" | grep -c "^[a-zA-Z0-9._-]* [0-9]" || true)
if [ "$PIP_STATUS" -eq 0 ]; then
  PIP_LINE="pip-audit: pa dobësi të njohura"
else
  PIP_LINE="pip-audit: GJETJE — $(echo "$PIP_REPORT" | grep -i "found .* vulnerab" | head -1)"
fi
if [ "$NPM_STATUS" -eq 0 ]; then
  NPM_LINE="npm audit: pa dobësi të njohura"
else
  NPM_LINE="npm audit: GJETJE — $(echo "$NPM_REPORT" | grep -iE "[0-9]+ .*vulnerabilit" | head -1)"
fi

URGENT=false
if [ "$PIP_STATUS" -ne 0 ] || [ "$NPM_STATUS" -ne 0 ]; then
  URGENT=true
fi

backend/.venv/bin/python - "$PIP_LINE" "$NPM_LINE" "$URGENT" <<'PYEOF'
import asyncio
import sys

sys.path.insert(0, "backend")

from app.services.ops_notify import notify_ops

pip_line, npm_line, urgent = sys.argv[1], sys.argv[2], sys.argv[3] == "true"
text = (
    "Skanimi javor i varësive (security_scan.sh):\n"
    f"• {pip_line}\n"
    f"• {npm_line}\n"
    "Raporti i plotë: data/security-scan.log"
)
ok = asyncio.run(notify_ops("siguri", text, urgent=urgent))
print(f"halim notified: {ok}")
PYEOF

echo "scan done: $PIP_LINE | $NPM_LINE"
