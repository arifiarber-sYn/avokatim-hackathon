#!/usr/bin/env bash
# Starts the full AvokatIM stack on this machine.
set -euo pipefail
cd "$(dirname "$0")"

echo "[1/3] Infrastruktura (Postgres + Redis + Caddy)..."
# Ne boot docker daemon mund te mos jete gati ende
for _ in $(seq 1 30); do
    docker info > /dev/null 2>&1 && break
    sleep 2
done
docker compose up -d --wait

echo "[2/3] Backend (FastAPI ne 127.0.0.1:8000)..."
if ! curl -sf http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
    (cd backend && .venv/bin/alembic upgrade head)
    nohup backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 \
        --app-dir backend >> data/backend.log 2>&1 &
fi
for _ in $(seq 1 30); do
    curl -sf http://127.0.0.1:8000/api/health > /dev/null 2>&1 && break
    sleep 1
done
curl -sf http://127.0.0.1:8000/api/health > /dev/null && echo "  Backend OK"

echo "[3/3] Frontend (Next.js ne 127.0.0.1:3000)..."
# Rindertim nese s'ka build OSE nese kodi eshte me i ri se build-i ekzistues.
# (Nje server i vjeter mbi nje build te ri jep 404 per chunks JS -> faqe bosh.)
NEEDS_BUILD=0
if [ ! -f frontend/.next/BUILD_ID ]; then
    NEEDS_BUILD=1
else
    NEWEST_SRC=$(find frontend/src frontend/public frontend/package.json \
        -type f -newer frontend/.next/BUILD_ID 2>/dev/null | head -1)
    [ -n "$NEWEST_SRC" ] && NEEDS_BUILD=1
fi
if [ "$NEEDS_BUILD" = "1" ]; then
    echo "  Kodi i frontend-it ka ndryshuar — po rindertohet..."
    (cd frontend && npm run build > /dev/null 2>&1)
fi
# Ndalo GJITHMONE serverin e vjeter te KETIJ projekti (identifikohet nga cwd,
# se emri "next-server" eshte i njejte per cdo projekt Next ne kete makine).
# Incidenti 2026-07-23: build manual + restart e linte serverin e vjeter gjalle
# me kod te vjeter ne memorie, sepse pkill ndodhte vetem kur ndryshonte kodi.
for pid in $(pgrep -f "next-serve[r]" 2>/dev/null || true); do
    if [ "$(readlink /proc/$pid/cwd 2>/dev/null)" = "$PWD/frontend" ]; then
        kill "$pid" 2>/dev/null || true
    fi
done
sleep 2
if ! curl -sf http://127.0.0.1:3000 > /dev/null 2>&1; then
    (cd frontend && nohup npm start >> ../data/frontend.log 2>&1 &)
fi
for _ in $(seq 1 60); do
    curl -sf -o /dev/null http://127.0.0.1:3000 && break
    sleep 1
done
curl -sf -o /dev/null http://127.0.0.1:3000 && echo "  Frontend OK"

IP=$(ip -4 addr show scope global | awk '/inet /{print $2}' | cut -d/ -f1 | head -1)
echo
echo "AvokatIM eshte gati:"
echo "  Lokalisht:    http://127.0.0.1:3000"
echo "  Nga rrjeti:   https://${IP}:8443   (certifikate lokale — prano paralajmerimin e shfletuesit)"
