#!/usr/bin/env bash
# NexusIQ-u tək əmrlə işə salır: Postgres + backend (8001) + frontend (3000).
# Artıq işləyəni təkrar başlatmır; sağlamlıq yoxlamasını gözləyib status verir.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$HOME/Library/Logs/nexusiq"
mkdir -p "$LOG_DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

backend_up() { curl -fsS -m2 "http://localhost:$BACKEND_PORT/api/v1/health" >/dev/null 2>&1; }
frontend_up() { [ "$(curl -s -m2 -o /dev/null -w '%{http_code}' "http://localhost:$FRONTEND_PORT" 2>/dev/null)" = "200" ]; }

echo "==> Postgres (postgresql@14)"
brew services start postgresql@14 >/dev/null 2>&1 || \
  echo "   qeyd: brew postgres başlamadı — əl ilə yoxla (port 5433)"

# ---- Backend ----
if backend_up; then
  echo "==> Backend onsuz da işləyir (:$BACKEND_PORT)"
else
  echo "==> Backend başladılır (:$BACKEND_PORT)"
  ( cd "$ROOT/backend" && BACKEND_PORT="$BACKEND_PORT" nohup .venv/bin/python -m uvicorn \
      app.main:app --host 127.0.0.1 --port "$BACKEND_PORT" --log-level warning \
      >> "$LOG_DIR/backend.log" 2>&1 & echo $! > "$LOG_DIR/backend.pid" )
  for _ in $(seq 1 60); do backend_up && break; sleep 1; done
  backend_up && echo "   backend hazır" || { echo "   XƏTA: backend qalxmadı — $LOG_DIR/backend.log"; exit 1; }
fi

# ---- Frontend ----
if frontend_up; then
  echo "==> Frontend onsuz da işləyir (:$FRONTEND_PORT)"
else
  if [ ! -f "$ROOT/frontend/.next/BUILD_ID" ]; then
    echo "==> Frontend production build"
    ( cd "$ROOT/frontend" && npm run build )
  fi
  echo "==> Frontend başladılır (:$FRONTEND_PORT)"
  ( cd "$ROOT/frontend" && nohup npm run start -- --port "$FRONTEND_PORT" \
      >> "$LOG_DIR/frontend.log" 2>&1 & echo $! > "$LOG_DIR/frontend.pid" )
  for _ in $(seq 1 60); do frontend_up && break; sleep 1; done
  frontend_up && echo "   frontend hazır" || { echo "   XƏTA: frontend qalxmadı — $LOG_DIR/frontend.log"; exit 1; }
fi

echo
"$ROOT/scripts/status.sh" || true
