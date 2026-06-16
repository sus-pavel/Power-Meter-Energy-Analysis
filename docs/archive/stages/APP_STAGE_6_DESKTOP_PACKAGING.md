# Stage 6 Desktop Packaging

PowerMeter Stage 6 packages the existing local-first FastAPI and React app as a macOS desktop app using Tauri.

## Architecture

```text
PowerMeter.app
├── Tauri desktop shell
│   └── loads frontend/dist
├── Contents/Resources/backend/
│   ├── powermeter-backend
│   └── _internal/
│       └── PyInstaller onedir runtime
├── supervised FastAPI backend process
│   └── binds to 127.0.0.1:8765
└── ~/Library/Application Support/PowerMeter/
    ├── app.sqlite
    ├── config/
    ├── logs/
    ├── exports/
    ├── reports/
    ├── cache/
    └── tmp/
```

The Tauri shell starts `Contents/Resources/backend/powermeter-backend` with `std::process::Command`, waits for `/api/health`, and terminates only the child process it launched when the app closes. The PyInstaller backend is not configured as a Tauri `externalBin` sidecar because onedir mode requires the executable plus `_internal` runtime files.

## Runtime Paths

Desktop mode is enabled with:

```bash
POWERMETER_DESKTOP_MODE=1
```

Desktop mode uses:

```text
~/Library/Application Support/PowerMeter/app.sqlite
~/Library/Application Support/PowerMeter/logs/backend.log
~/Library/Application Support/PowerMeter/logs/desktop.log
```

Development mode keeps the existing repository-local database unless `POWERMETER_APP_DATA_DIR` or `POWERMETER_DB_PATH` is set.

## Build Steps

```bash
scripts/build_frontend.sh
scripts/build_backend_binary.sh
scripts/build_macos_app.sh
```

The full app build outputs:

```text
src-tauri/target/release/bundle/macos/PowerMeter.app
```

If the host has the required macOS packaging tools available, Tauri also attempts to create a DMG under:

```text
src-tauri/target/release/bundle/dmg/
```

## Scripts

- `scripts/build_frontend.sh` installs frontend dependencies and builds `frontend/dist`.
- `scripts/build_backend_binary.sh` installs Python backend dependencies plus PyInstaller, then creates the backend sidecar.
- `scripts/build_macos_app.sh` runs the full frontend, backend, and Tauri pipeline, then copies the PyInstaller onedir into `PowerMeter.app/Contents/Resources/backend/`.
- `scripts/run_desktop_dev.sh` runs backend and Vite in desktop mode for local testing.
- `scripts/reset_desktop_app_data.sh` deletes the desktop app data directory after explicit confirmation.

## Known Limitations

- The app is unsigned and not notarized in Stage 6.
- The backend port is fixed at `127.0.0.1:8765`.
- If another process owns port `8765`, startup reports a diagnostic error instead of selecting a random port.
- First-run password change is surfaced as a visible warning; a dedicated password-change screen is deferred to Stage 6.1.
