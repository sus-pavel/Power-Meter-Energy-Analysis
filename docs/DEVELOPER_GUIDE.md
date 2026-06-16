# Developer Guide

PowerMeter App combines a FastAPI backend, React/Vite frontend, and Tauri v2 macOS shell.

## Development Servers

Backend:

```bash
uvicorn backend.app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend uses `VITE_API_BASE_URL` when set. Otherwise browser development mode defaults to `http://127.0.0.1:8000`. Desktop mode uses `http://127.0.0.1:8765`.

## Desktop Build

```bash
scripts/build_macos_app.sh
```

This runs the frontend build, builds the PyInstaller backend onedir output, builds the Tauri `.app`, and copies the backend runtime into:

```text
src-tauri/target/release/bundle/macos/PowerMeter.app/Contents/Resources/backend/
```

The backend executable path inside the bundle is:

```text
Contents/Resources/backend/powermeter-backend
```

## Validation

Recommended checks before release:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/powermeter-pycache python3 -m compileall backend/app backend/desktop_entry.py
cd frontend && npm run build
scripts/build_backend_binary.sh
scripts/build_macos_app.sh
```

Manual desktop checks are listed in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

## Scripts

User-facing scripts are kept in `scripts/` and are executable:

- `scripts/build_frontend.sh` - builds the React/Vite frontend.
- `scripts/build_backend_binary.sh` - builds the PyInstaller backend runtime.
- `scripts/build_macos_app.sh` - builds `PowerMeter.app` and copies the backend runtime into the app bundle.
- `scripts/reset_desktop_app_data.sh` - deletes `~/Library/Application Support/PowerMeter/` after confirmation.
- `scripts/run_desktop_dev.sh` - starts desktop-oriented local development services.

## Code Boundaries

- Do not rewrite DRPI formulas or SSA mathematical logic during packaging work.
- Do not remove the original research prototype modules.
- Do not introduce cloud services, Docker, auto-update, or Windows/Linux packaging as part of the macOS beta.
