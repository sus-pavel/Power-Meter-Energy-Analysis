#!/usr/bin/env bash
# Build the FastAPI backend as a PyInstaller onedir runtime.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYINSTALLER_CONFIG_DIR="${PYINSTALLER_CONFIG_DIR:-/private/tmp/powermeter-pyinstaller}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/private/tmp/powermeter-matplotlib}"

mkdir -p "$PYINSTALLER_CONFIG_DIR" "$MPLCONFIGDIR"

cd "$ROOT_DIR"
"$PYTHON_BIN" -m pip install -r requirements.txt pyinstaller

cd "$ROOT_DIR/backend"
"$PYTHON_BIN" -m PyInstaller pyinstaller_backend.spec --clean --noconfirm

if [[ ! -x "$ROOT_DIR/backend/dist/powermeter-backend/powermeter-backend" ]]; then
  echo "Backend sidecar was not created at backend/dist/powermeter-backend/powermeter-backend" >&2
  exit 1
fi

case "$(uname -m)" in
  arm64|aarch64)
    TARGET_TRIPLE="aarch64-apple-darwin"
    ;;
  x86_64)
    TARGET_TRIPLE="x86_64-apple-darwin"
    ;;
  *)
    echo "Unsupported macOS architecture: $(uname -m)" >&2
    exit 1
    ;;
esac

cp "$ROOT_DIR/backend/dist/powermeter-backend/powermeter-backend" \
  "$ROOT_DIR/backend/dist/powermeter-backend/powermeter-backend-$TARGET_TRIPLE"
chmod +x "$ROOT_DIR/backend/dist/powermeter-backend/powermeter-backend-$TARGET_TRIPLE"

rm -rf "$ROOT_DIR/backend/dist/powermeter-backend-resource"
mkdir -p "$ROOT_DIR/backend/dist/powermeter-backend-resource"
cp -R -L "$ROOT_DIR/backend/dist/powermeter-backend/." "$ROOT_DIR/backend/dist/powermeter-backend-resource/"
