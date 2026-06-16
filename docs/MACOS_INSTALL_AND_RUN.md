# macOS Install and Run

PowerMeter App v0.2.0 is packaged as a local macOS desktop beta.

## Build

From the repository root:

```bash
scripts/build_macos_app.sh
```

Expected app output:

```text
src-tauri/target/release/bundle/macos/PowerMeter.app
```

## Run

Open `PowerMeter.app`. The app starts the local backend automatically and waits for backend health before showing the normal UI.

The backend binds only to:

```text
127.0.0.1:8765
```

## App Data

PowerMeter stores desktop runtime data in:

```text
~/Library/Application Support/PowerMeter/
```

SQLite database:

```text
~/Library/Application Support/PowerMeter/app.sqlite
```

Logs:

```text
~/Library/Application Support/PowerMeter/logs/backend.log
~/Library/Application Support/PowerMeter/logs/desktop.log
```

## First Run Login

The first run creates the default local administrator if no users exist:

```text
admin / admin
```

The UI shows a warning while the default admin password is still active. Change the admin password from User Administration before operational use.

## Reset App Data

```bash
scripts/reset_desktop_app_data.sh
```

The script requires typing `RESET` before it deletes the app data directory.

## Build Scripts

- `scripts/build_frontend.sh` builds the React/Vite frontend.
- `scripts/build_backend_binary.sh` builds the FastAPI backend onedir runtime.
- `scripts/build_macos_app.sh` runs the full macOS app build pipeline.
- `scripts/run_desktop_dev.sh` starts local desktop-oriented development services.

## Gatekeeper

PowerMeter App v0.2.0 does not include Developer ID signing or notarization. macOS may show an unsigned app warning. Developer ID signing, notarization, and a polished installer flow are beta packaging follow-up work.
