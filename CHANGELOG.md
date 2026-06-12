# Changelog

All notable changes to PowerMeter will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project is intended to use semantic versioning for public releases.

## [v0.1.0] - Unreleased

### Added

- Modbus TCP data collection from YAML-defined devices.
- Support for holding and input registers.
- Register decoding for `float32`, `float32_swapped`, `uint16`, `int16`, `uint32`, and `int32`.
- Configurable Modbus address modes: `minus_400000`, `minus_400001`, and `raw`.
- Diagnostic Modbus collector for register-offset and decoding validation.
- Batch SQLite writer with configurable PRAGMA settings, retry behavior, batch size, and flush interval.
- Raw measurement storage in `raw_data`.
- Aggregation service for 5, 10, 15, 30, and 60 minute windows.
- Raw-data retention policy with a default of 24 hours.
- DRPI calculation for individual meters and total active-power consumption.
- DRPI result storage with `F1`, `F2`, `F3`, `R_raw`, and `DRPI`.
- SSA decomposition engine with trajectory matrix construction, SVD, reconstructed components, contribution calculation, W-correlation, and KMeans clustering.
- FastAPI dashboard application with overview, history, DRPI, and SSA pages.
- JSON API endpoints for overview, history, DRPI, and SSA analysis.
- Swagger/OpenAPI documentation through FastAPI at `/docs`.
- Raspberry Pi deployment documentation.
- English README entry point, Russian README, citation support, method docs, roadmap, contribution guide, release plan, demo-mode plan, GitHub visibility guide, and repository review.

### Known Limitations

- No implemented demo mode yet.
- No complete automated test suite yet.
- SSA runs are computed on demand through the web/API layer and are not persisted as versioned research runs.
