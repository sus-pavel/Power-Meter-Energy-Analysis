# App Stage 3.3: Operational Dashboard

Stage 3.3 adds operational visibility after devices are configured. It does not add a polling engine, realtime charts, DRPI, SSA, WebSockets, Tauri, Docker, or packaging.

## Purpose

The dashboard and operations page answer:

- how many devices are configured and enabled;
- which devices are online, offline, unknown, disabled, or error;
- when each device was last seen;
- whether scan jobs or candidates need attention;
- whether measurement data exists;
- whether devices are ready for future polling based on enabled register maps.

## Routes

- `/dashboard`: compact operational overview for all authenticated users.
- `/operations`: dedicated monitoring page for `admin`, `chief_engineer`, and `analyst`.

## Backend Endpoints

Added lightweight read-only endpoints:

- `GET /api/operations/status`
- `GET /api/operations/devices`
- `GET /api/operations/recent-measurements`
- `GET /api/operations/events`

These endpoints summarize existing application tables and, when present, the prototype `raw_data` measurement table.

## Components

- `OperationalStatusCards`
- `AttentionPanel`
- `DeviceStatusTable`
- `RecentActivityList`
- `MeasurementAvailabilityCard`
- `OperationalStatusBadge`
- `LastSeenIndicator`

## Refresh Strategy

- Dashboard queries refresh every 10 seconds.
- Operations page queries refresh every 5 seconds.
- TanStack Query handles polling.
- No WebSocket or realtime streaming is used.

## Status And Readiness

Device statuses:

- `online`
- `offline`
- `unknown`
- `disabled`
- `error`

Polling readiness:

- `ready`: enabled device with enabled registers.
- `no_registers`: enabled device with no enabled registers.
- `disabled`: disabled device.
- `unknown`: reserved for future acquisition state.

## Limitations

- Online status is inferred from recent measurement rows if they exist.
- If no measurement table exists, enabled devices are shown as `unknown`.
- No active polling worker is implemented in this stage.
- Last error is reserved for future acquisition diagnostics.

## Next Stage

Stage 4 should introduce the application polling control plane: safe scheduler controls, per-device acquisition state, polling logs, error classification, and eventually chart-ready measurement APIs.
