# Release Plan

## Version

`v0.1.0`

## Release Title

Research Prototype Release

## Release Goal

Publish PowerMeter as a clear, citable, and evaluable open-source research prototype for Modbus TCP energy monitoring, local dashboarding, demand-response potential assessment, and SSA-based electrical load pattern analysis.

## Capabilities

The `v0.1.0` release should include:

- Modbus TCP polling from YAML-configured devices.
- Support for common register types and address-offset modes.
- SQLite raw-data persistence.
- Aggregated time-series tables for 5, 10, 15, 30, and 60 minute windows.
- DRPI calculation for individual meters and `TOTAL`.
- SSA analysis through the web dashboard and API.
- FastAPI dashboards for overview, history, DRPI, and SSA.
- Swagger/OpenAPI documentation at `/docs`.
- Raspberry Pi deployment instructions.
- English README, Russian README, citation metadata, and method documentation.

## Supported Environments

Expected environments:

- Python 3.11 or newer.
- macOS, Linux, or Windows for local development.
- Raspberry Pi OS or another Linux distribution for edge deployment.
- SQLite through Python's standard library.
- Modbus TCP meters or a Modbus TCP gateway.

Recommended runtime pattern:

- data pipeline: `python main.py`;
- web application: `uvicorn web.app:app --host 0.0.0.0 --port 8000`.

## Limitations

Document these limitations clearly in the release notes:

- The project is a research prototype, not a certified energy management system.
- No demo mode is implemented yet.
- Real Modbus hardware or a future simulator is required for live data collection.
- No full automated test suite is included yet.
- The repository does not yet provide Docker Compose or packaged installers.
- Screenshots must be added manually before a polished public showcase.
- DOI is not available until Zenodo integration is enabled and a GitHub release is archived.
- DRPI estimates flexibility potential from load profiles and does not guarantee controllable demand-response capacity.

## Pre-Release Checklist

- Verify `README.md` is the English entry point.
- Verify `README.ru.md` contains Russian documentation.
- Verify `CITATION.cff` is valid.
- Verify `CHANGELOG.md` has a `v0.1.0` section.
- Verify all docs links resolve.
- Add public-safe screenshots.
- Confirm `config/devices.yaml` is not committed.
- Confirm `data/energy.db`, `data/energy.db-wal`, and `data/energy.db-shm` are not committed.
- Confirm no `.DS_Store` files are committed.
- Run a local import or smoke check.
- Create the GitHub release tag `v0.1.0`.
- Archive the release with Zenodo.

## Suggested Release Notes

```text
PowerMeter v0.1.0 - Research Prototype Release

This initial public release provides a local-first Modbus TCP energy monitoring platform with SQLite storage, real-time FastAPI dashboards, DRPI demand-response potential assessment, and SSA-based electrical load pattern analysis.

Highlights:
- Modbus TCP collection from YAML-configured devices.
- Batch SQLite writer and aggregation pipeline.
- DRPI calculation for meters and total consumption.
- Interactive overview, history, DRPI, and SSA dashboards.
- JSON API and Swagger/OpenAPI documentation.
- Raspberry Pi deployment guide.
- Citation metadata and research-method documentation.

Limitations:
- Research prototype release.
- No implemented demo mode yet.
- No committed screenshot gallery yet.
- No complete automated test suite yet.
- DOI pending Zenodo integration.
```

## Future Plans After Release

- Implement demo mode.
- Add automated tests and CI.
- Add Docker or packaged deployment examples.
- Add public demo screenshots and sample data.
- Persist SSA runs for reproducibility.
- Expand NILM-based feedback research integration.
