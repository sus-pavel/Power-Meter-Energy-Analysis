# Roadmap

This roadmap describes documentation, engineering, and research directions for PowerMeter. It does not change the current project scope: a local-first Modbus TCP energy monitoring and analytics platform.

## Short-Term

- Add real screenshots for `/overview`, `/history`, `/drpi`, `/ssa`, and `/docs`.
- Create the first public GitHub release as `v0.1.0`.
- Add Zenodo integration for archival DOI generation.
- Add a public demo dataset or documented demo workflow.
- Add automated smoke tests for importability, configuration parsing, and core DRPI/SSA calculations.
- Add API examples generated from known fixture data.
- Add a root-level issue template and pull request template.
- Translate or summarize Raspberry Pi deployment instructions in English.

## Medium-Term

- Implement a demo mode with simulated Modbus devices and synthetic load profiles.
- Add database migration/versioning strategy for SQLite schema changes.
- Add configuration validation with clearer startup errors.
- Add optional export endpoints for CSV or Parquet.
- Add service health endpoints for pipeline status.
- Add packaged deployment options, such as Docker Compose or a documented `systemd` pair for pipeline and web app.
- Persist SSA runs and cluster reconstructions when needed for repeatable research.
- Add more complete tests around Modbus decoding, aggregation windows, DRPI edge cases, and SSA response validation.
- Add reproducible benchmark notebooks or scripts for published figures.

## Long-Term Vision

- Support multi-site or multi-line monitoring while preserving local-first deployment.
- Add NILM-based feedback loops for demand-response decision support.
- Integrate event-based metrics for load switching and demand-response validation.
- Support richer research exports with metadata and citation information.
- Add role-aware dashboards for operations, energy managers, and researchers.
- Publish reference datasets or anonymized examples for external validation.
- Maintain versioned method documentation so results can be reproduced across releases.
