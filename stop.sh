#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")"

pkill -f "uvicorn app.main:app" 2>/dev/null && echo "Backend u ndal"
pkill -f "next start" 2>/dev/null && echo "Frontend u ndal"
docker compose stop
echo "AvokatIM u ndal."
