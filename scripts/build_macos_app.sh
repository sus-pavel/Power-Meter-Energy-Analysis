#!/usr/bin/env bash
# Build PowerMeter.app and copy the PyInstaller backend runtime into the bundle.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT_DIR/scripts/build_frontend.sh"
"$ROOT_DIR/scripts/build_backend_binary.sh"

cd "$ROOT_DIR"
"$ROOT_DIR/frontend/node_modules/.bin/tauri" build --bundles app

APP_PATH="$ROOT_DIR/src-tauri/target/release/bundle/macos/PowerMeter.app"
DMG_DIR="$ROOT_DIR/src-tauri/target/release/bundle/dmg"
RESOURCE_BACKEND_DIR="$APP_PATH/Contents/Resources/backend"

if [[ -d "$APP_PATH" ]]; then
  rm -rf "$RESOURCE_BACKEND_DIR"
  mkdir -p "$APP_PATH/Contents/Resources"
  cp -R "$ROOT_DIR/backend/dist/powermeter-backend-resource" "$RESOURCE_BACKEND_DIR"
  echo "Created $APP_PATH"
else
  echo "PowerMeter.app was not found at $APP_PATH" >&2
  exit 1
fi

if compgen -G "$DMG_DIR/*.dmg" > /dev/null; then
  echo "Created DMG:"
  ls "$DMG_DIR"/*.dmg
else
  echo "No DMG was created."
fi
