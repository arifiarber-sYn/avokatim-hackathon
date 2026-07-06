#!/usr/bin/env bash
# Starts the full BoraLaw stack on this machine.
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
if ! curl -sf http://127.0.0.1:3000 > /dev/null 2>&1; then
    # Rindertim vetem nese s'ka build ekzistues (pas ndryshimeve ne kod fshije frontend/.next)
    if [ ! -d frontend/.next ]; then
        (cd frontend && npm run build > /dev/null 2>&1)
    fi
    (cd frontend && nohup npm start >> ../data/frontend.log 2>&1 &)
fi
for _ in $(seq 1 60); do
    curl -sf -o /dev/null http://127.0.0.1:3000 && break
    sleep 1
done
curl -sf -o /dev/null http://127.0.0.1:3000 && echo "  Frontend OK"

IP=$(ip -4 addr show scope global | awk '/inet /{print $2}' | cut -d/ -f1 | head -1)
echo
echo "BoraLaw eshte gati:"
echo "  Lokalisht:    http://127.0.0.1:3000"
echo "  Nga rrjeti:   https://${IP}:8443   (certifikate lokale — prano paralajmerimin e shfletuesit)"
