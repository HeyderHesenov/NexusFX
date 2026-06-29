#!/usr/bin/env bash
# dev.sh ilə başladılan NexusIQ proseslərini dayandırır (yalnız öz PID-lərimizi).
set -uo pipefail

LOG_DIR="$HOME/Library/Logs/nexusiq"

stop_one() {
  local name="$1" pidfile="$LOG_DIR/$1.pid"
  if [ -f "$pidfile" ]; then
    local pid; pid="$(cat "$pidfile" 2>/dev/null || true)"
    if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null && echo "==> $name dayandırıldı (pid $pid)"
    else
      echo "==> $name işləmir"
    fi
    rm -f "$pidfile"
  else
    echo "==> $name üçün pid faylı yox (dev.sh ilə başlamayıb?)"
  fi
}

stop_one backend
stop_one frontend
echo "Bitdi. (Postgres toxunulmadı.)"
