# App Stage 6 Desktop Preparation

Stage 6 is expected to package PowerMeter as a local desktop application. Stage 5 does not implement packaging, but it prepares the codebase for that work.

## Expected Direction

The likely direction is Tauri:

- React/Vite frontend as the window UI.
- FastAPI backend as a local sidecar process.
- SQLite database stored in an app data directory.

## Backend Sidecar Idea

The backend can run as one local process:

```bash
uvicorn backend.app.main:app
```

For desktop packaging, a wrapper can launch this process on a local port and point the frontend to it.

## Local App Data Directory

The app database path is configurable:

```bash
POWERMETER_APP_DB=/path/to/powermeter_app.db
```

Desktop packaging should map this to the platform app data directory instead of the repository `data/` folder.

## Frontend API Base URL

The frontend API base URL is configurable:

```bash
VITE_API_BASE_URL=http://127.0.0.1:<port>/api
```

This allows the packaged frontend to talk to the backend sidecar without hardcoded development proxy assumptions.

## Known Blockers

- Need sidecar process supervision.
- Need port allocation strategy.
- Need database migration/version handling.
- Need default password flow before real distribution.
- Need local logs directory.
- Need packaging-specific security review.

## Required Checks Before Packaging

- Backend starts and stops cleanly.
- Background polling and analytics services shut down promptly.
- Frontend production build passes.
- SQLite path resolves outside the repository.
- No network scanning starts automatically.
- No Modbus writes are implemented.
