# PowerMeter App Architecture

PowerMeter now has two product directions that should stay deliberately separate.

## Branches

`Base_Research_Prototype` preserves the research prototype: Modbus polling, SQLite writes, aggregation, DRPI, SSA, and the existing dashboard modules.

`App` is the product branch. It keeps the prototype available, but starts adding a local-first application backend around users, roles, device management, audit logging, and future packaging.

## Backend Layout

The application backend lives under `backend/app`:

```text
backend/app/
  main.py
  core/
  models/
  schemas/
  services/
  api/
```

The existing prototype modules remain in place:

```text
core/
services/
web/
config/
main.py
```

## Roles

PowerMeter uses four roles:

- `admin`: manages users, roles, devices, settings, database, and audit logs.
- `chief_engineer`: manages Modbus TCP devices and uses dashboards and analytics.
- `analyst`: views dashboards and analytics, and exports analytical data.
- `guest`: read-only dashboard access with sensitive device details hidden where practical.

## Future Modbus Discovery Workflow

Stage 2 will add a safe discovery flow:

1. Scan a configured IP range.
2. Check Modbus TCP port `502`.
3. Test Modbus TCP connectivity.
4. Scan configured `unit_id` values.
5. Probe selected registers safely.
6. Save discovered candidates.
7. Promote candidates into managed devices.

Stage 1 only exposes a placeholder probe endpoint and performs no network scanning.

## Future Desktop Packaging

The app backend is designed to be wrapped later by Tauri or a similar desktop shell. The target model is local SQLite storage, local FastAPI backend, and a frontend that can run in the desktop wrapper while retaining the current research tools for analytics.
