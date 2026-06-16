# Desktop Troubleshooting

## Backend Does Not Start

Check:

```text
~/Library/Application Support/PowerMeter/logs/backend.log
~/Library/Application Support/PowerMeter/logs/desktop.log
```

Confirm that the backend runtime exists inside the app bundle:

```text
PowerMeter.app/Contents/Resources/backend/powermeter-backend
PowerMeter.app/Contents/Resources/backend/_internal/
```

The source PyInstaller output should also exist at:

```text
backend/dist/powermeter-backend/powermeter-backend
```

## Port 8765 Busy

PowerMeter App v0.2.0 uses a fixed local port:

```text
127.0.0.1:8765
```

If another process owns the port, PowerMeter reports `port_in_use`. It does not kill the existing process. Stop the other process yourself and reopen PowerMeter.

## Database Initialization Failed

The desktop database should be:

```text
~/Library/Application Support/PowerMeter/app.sqlite
```

The backend startup is idempotent and creates missing Stage 1 through Stage 5 tables. It does not perform destructive migrations.

## Frontend Cannot Connect

In desktop mode the frontend API base is:

```text
http://127.0.0.1:8765/api
```

Open:

```text
http://127.0.0.1:8765/api/health
http://127.0.0.1:8765/api/desktop/diagnostics
```

Both should respond while the desktop app is running.

## Reset First-Run State

Run:

```bash
scripts/reset_desktop_app_data.sh
```

Then reopen `PowerMeter.app`.
