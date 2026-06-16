#!/usr/bin/env bash
# Delete the local macOS PowerMeter app data directory after confirmation.
set -euo pipefail

APP_DATA_DIR="${POWERMETER_APP_DATA_DIR:-$HOME/Library/Application Support/PowerMeter}"

echo "This will delete:"
echo "$APP_DATA_DIR"
read -r -p "Type RESET to continue: " confirmation

if [[ "$confirmation" != "RESET" ]]; then
  echo "Reset cancelled."
  exit 0
fi

rm -rf "$APP_DATA_DIR"
echo "Deleted $APP_DATA_DIR"
