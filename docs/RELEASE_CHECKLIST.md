# Release Checklist

Use this checklist before tagging PowerMeter App v0.2.0 macOS desktop beta.

## Automated Checks

- [ ] Backend compile check passes:
  `PYTHONPYCACHEPREFIX=/private/tmp/powermeter-pycache python3 -m compileall backend/app backend/desktop_entry.py`
- [ ] Backend tests pass if tests are present.
- [ ] Frontend production build passes:
  `cd frontend && npm run build`
- [ ] PyInstaller backend build passes:
  `scripts/build_backend_binary.sh`
- [ ] Tauri/macOS build passes:
  `scripts/build_macos_app.sh`

## Packaged App Checks

- [ ] `PowerMeter.app` launches.
- [ ] Backend sidecar starts automatically.
- [ ] `GET http://127.0.0.1:8765/api/health` returns `status: ok`.
- [ ] `GET http://127.0.0.1:8765/api/desktop/diagnostics` returns app data paths.
- [ ] SQLite database is stored in `~/Library/Application Support/PowerMeter/app.sqlite`.
- [ ] Backend and desktop logs are written under `~/Library/Application Support/PowerMeter/logs/`.
- [ ] Login works.
- [ ] Dashboard opens.
- [ ] Discovery works on a test network.
- [ ] A known Modbus device can be discovered and promoted.
- [ ] Polling starts and stops.
- [ ] Trends page loads.
- [ ] DRPI page loads.
- [ ] SSA page loads.
- [ ] Closing the app terminates the backend sidecar.
- [ ] Port `8765` is released after app close.
- [ ] No orphan `powermeter-backend` process remains.
- [ ] Reopening the app reuses the existing Application Support directory.
- [ ] App data reset script works:
  `scripts/reset_desktop_app_data.sh`

## Release Notes

- [ ] Known limitations are listed in `CHANGELOG.md`.
- [ ] Gatekeeper unsigned-app warning is documented.
- [ ] No cloud, Docker, auto-update, Windows, or Linux packaging claims are added.
