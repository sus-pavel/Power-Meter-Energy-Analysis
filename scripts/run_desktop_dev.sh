#!/usr/bin/env bash
# Run backend and frontend development servers for desktop-oriented testing.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DATA_DIR="${POWERMETER_APP_DATA_DIR:-$HOME/Library/Application Support/PowerMeter}"
PORT="${POWERMETER_PORT:-8765}"

mkdir -p "$APP_DATA_DIR"/{config,logs,exports,reports,cache,tmp}

export POWERMETER_DESKTOP_MODE=1
export POWERMETER_APP_DATA_DIR="$APP_DATA_DIR"
export POWERMETER_DB_PATH="${POWERMETER_DB_PATH:-$APP_DATA_DIR/app.sqlite}"
export POWERMETER_PORT="$PORT"
export VITE_API_BASE_URL="http://127.0.0.1:$PORT/api"
export VITE_POWERMETER_DESKTOP=1

cd "$ROOT_DIR"
python3 -m backend.desktop_entry &
BACKEND_PID=$!

cleanup() {
  if kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

for _ in {1..90}; do
  if curl -fsS "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

cd "$ROOT_DIR/frontend"
npm run dev
