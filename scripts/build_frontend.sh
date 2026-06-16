#!/usr/bin/env bash
# Build the React/Vite frontend for production desktop packaging.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR/frontend"
npm install
npm run build
