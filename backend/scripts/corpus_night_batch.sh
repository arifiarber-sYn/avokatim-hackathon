#!/usr/bin/env bash
# Nightly DE corpus batch (D-059 F2): pulls the next slice of federal case
# law from rechtsprechung-im-internet and, when an openlegaldata dump is
# present, the next slice of instance-court decisions. Both importers are
# resume-safe (DB reference check + unique index), so a fixed --limit per
# night grows the corpus without ever hammering the sources or the embedder.
#
# Usage:  corpus_night_batch.sh [limit]          (default 2000)
# Dump:   put the openlegaldata dump at data/corpus/oldp-cases.jsonl.gz
# Log:    data/corpus-batch.log
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

LIMIT="${1:-2000}"
LOG="$ROOT/data/corpus-batch.log"
DUMP="$ROOT/data/corpus/oldp-cases.jsonl.gz"
PY="$ROOT/backend/.venv/bin/python"

cd "$ROOT/backend"
echo "=== corpus batch $(date -Is) limit=$LIMIT ===" >> "$LOG"

"$PY" scripts/import_de_rechtsprechung.py --limit "$LIMIT" >> "$LOG" 2>&1 || \
  echo "rechtsprechung importer failed (see above)" >> "$LOG"

if [ -f "$DUMP" ]; then
  "$PY" scripts/import_de_openlegaldata.py --file "$DUMP" --limit "$LIMIT" >> "$LOG" 2>&1 || \
    echo "openlegaldata importer failed (see above)" >> "$LOG"
else
  echo "no openlegaldata dump at $DUMP — skipping instance courts" >> "$LOG"
fi

echo "=== corpus batch done $(date -Is) ===" >> "$LOG"
