# PowerMeter

[English](README.md) | [Русский](README.ru.md)

PowerMeter is a local-first energy monitoring and analytics platform for Modbus TCP power meters. It discovers meters on a local network, probes candidate devices, promotes verified devices into management, polls measurements, stores data in SQLite, and presents operational dashboards with historical trends, DRPI demand-response analytics, and SSA time-series decomposition.

The current target is **PowerMeter.app for macOS**: a Tauri desktop shell that starts a bundled FastAPI backend and serves the React/Vite frontend locally. PowerMeter is not a cloud SaaS product and is not a full SCADA or control platform. It is built for local monitoring, lab validation, pilot deployments, and analytics workflows around energy data.

Keywords: energy-monitoring, modbus-tcp, fastapi, react, tauri, sqlite, demand-response, time-series, ssa, power-systems.

## Workflow

```text
Modbus TCP discovery
  → candidate probing
  → device promotion
  → managed devices
  → polling
  → measurements
  → aggregation
  → trends
  → DRPI
  → SSA
  → dashboard
```

## Tech Stack

- Backend: FastAPI, Uvicorn, Pydantic, SQLite.
- Frontend: React, Vite, TypeScript.
- Desktop: Tauri v2 for macOS packaging and backend process supervision.
- Field protocol: Modbus TCP with safer Unit ID discovery modes.
- Analytics: DRPI demand-response potential assessment and SSA time-series decomposition.

## Key Features

- Local desktop operation with `PowerMeter.app`.
- FastAPI backend sidecar launched and stopped by the desktop shell.
- SQLite app database under `~/Library/Application Support/PowerMeter/`.
- Modbus TCP discovery with configurable network targets.
- Safer Unit ID scan modes for real-device validation.
- Candidate probing, fingerprinting, and device promotion.
- Managed device inventory and polling controls.
- SQLite measurement storage and aggregation.
- Historical trends UI.
- DRPI demand-response potential analytics.
- SSA time-series decomposition analytics.
- React dashboard and analytics UI.
- Desktop troubleshooting and app-data reset scripts.

## Current Limitations

- The macOS beta app is unsigned and not notarized, so Gatekeeper may warn on first launch.
- This is a local beta release, not a hardened production distribution.
- Modbus register maps may require manual configuration for each meter model.
- PowerMeter is not a SCADA/control platform and does not issue control commands.
- There is no cloud sync, hosted service, or multi-site cloud account model.
- Windows and Linux packaging are not implemented yet.
- Auto-update and notarized installer UX are future work.

## macOS Desktop Quick Start

Build the app:

```bash
scripts/build_macos_app.sh
```

The app bundle is created at:

```text
src-tauri/target/release/bundle/macos/PowerMeter.app
```

Launch it from Finder or with:

```bash
open -n src-tauri/target/release/bundle/macos/PowerMeter.app
```

The packaged backend listens only on:

```text
http://127.0.0.1:8765
```

App data and logs live under:

```text
~/Library/Application Support/PowerMeter/
```

For detailed instructions, see [docs/MACOS_INSTALL_AND_RUN.md](docs/MACOS_INSTALL_AND_RUN.md) and [docs/DESKTOP_TROUBLESHOOTING.md](docs/DESKTOP_TROUBLESHOOTING.md).

## Development Quick Start

Backend development mode:

```bash
uvicorn backend.app.main:app --reload
```

Frontend development mode:

```bash
cd frontend
npm install
npm run dev
```

By default the browser frontend uses `http://127.0.0.1:8000` unless `VITE_API_BASE_URL` is set. Desktop mode uses `http://127.0.0.1:8765`.

## Documentation

- [Architecture](docs/APP_ARCHITECTURE.md)
- [User Guide](docs/USER_GUIDE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [macOS Install and Run](docs/MACOS_INSTALL_AND_RUN.md)
- [Desktop Troubleshooting](docs/DESKTOP_TROUBLESHOOTING.md)
- [Modbus Discovery and Onboarding](docs/MODBUS_DISCOVERY_AND_ONBOARDING.md)
- [DRPI and SSA Analytics](docs/ANALYTICS_DRPI_SSA.md)
- [Release Checklist](docs/RELEASE_CHECKLIST.md)
- [Security Notes](docs/SECURITY_NOTES.md)

Historical stage notes are archived in [docs/archive/stages](docs/archive/stages).

## License

See [LICENSE](LICENSE).
