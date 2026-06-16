# Changelog

All notable changes to PowerMeter will be documented in this file.

## PowerMeter App v0.2.0 — macOS Desktop Beta

### Added

- Added macOS desktop packaging with Tauri v2.
- Added FastAPI backend sidecar mode.
- Added local SQLite app data directory.
- Added Modbus TCP discovery/probing/promotion workflow.
- Added configurable Unit ID discovery modes.
- Added polling engine.
- Added historical trends.
- Added DRPI analytics.
- Added SSA analytics.
- Added React dashboard and analytics UI.
- Added desktop troubleshooting/reset scripts.

### Known Limitations

- macOS app is unsigned and not notarized.
- Beta packaging currently targets macOS only.
- Modbus register maps may require manual configuration for specific meters.
- PowerMeter is local-first and has no cloud sync.
- PowerMeter is not a SCADA/control platform.
- No auto-update flow is included.
- Automated end-to-end test coverage is still limited.

## v0.1.0 - Research Prototype Baseline

### Added

- Modbus TCP data collection from YAML-defined devices.
- SQLite writer, aggregation windows, DRPI calculation, and SSA decomposition modules.
- Original FastAPI dashboard pages and method documentation.
