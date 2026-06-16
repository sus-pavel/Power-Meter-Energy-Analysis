# Security Notes

PowerMeter App v0.2.0 is a local-first macOS beta.

## Desktop Runtime

- Backend binds only to `127.0.0.1` in packaged desktop mode.
- The default desktop port is `8765`.
- Tauri checks whether port `8765` is occupied before launching the backend.
- If the port is already occupied, the app reports `port_in_use` and does not kill the existing process.
- On shutdown, the desktop shell terminates only the child process it launched.

## Local Data

Runtime data is outside the repository and outside the `.app` bundle:

```text
~/Library/Application Support/PowerMeter/
```

The SQLite database is:

```text
~/Library/Application Support/PowerMeter/app.sqlite
```

Logs are:

```text
~/Library/Application Support/PowerMeter/logs/backend.log
~/Library/Application Support/PowerMeter/logs/desktop.log
```

## Secrets

- Do not commit production secrets, private device maps, credentials, or real site data.
- The backend should create or use local secrets from the app data directory in desktop mode.
- Passwords and JWT tokens must not be logged.
- Frontend storage should remain minimal; JWT storage is the current beta tradeoff.

## Network Use

PowerMeter should be used only on networks where scanning and Modbus access are authorized. Discovery scans should start narrow and expand only when necessary.
