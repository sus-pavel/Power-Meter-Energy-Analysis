# Repository Review

This review summarizes the current state of PowerMeter as an open-source research software project.

## Strengths

### Architecture

- Clear separation between data collection, writing, aggregation, analytics, and presentation.
- Local-first SQLite architecture is practical for pilot deployments, laboratories, and Raspberry Pi installations.
- YAML configuration keeps meter/register mapping outside the source code.
- The collector normalizes Modbus measurements into a simple record structure before persistence.
- The queue-based design decouples field polling from database writes.
- Aggregation tables provide useful time scales for dashboards and analytics.
- FastAPI provides both human-facing dashboards and machine-readable API documentation.

### Engineering Decisions

- The diagnostic collector is valuable for validating Modbus offsets, function codes, register counts, and word order before production use.
- Batch writing and SQLite WAL settings are appropriate for lightweight edge deployments.
- DRPI calculation is isolated in `core/drpi_engine.py`, separate from orchestration.
- SSA decomposition and clustering are isolated in `core/ssa_engine.py`, making method review easier.
- Ignored local files include `config/devices.yaml` and runtime data under `data/`, which helps prevent accidental disclosure of private site data.

### Research Value

- The project connects real industrial measurement workflows with demand-response analytics.
- DRPI provides a concrete index for comparing flexibility potential across sources and periods.
- SSA analysis supports interpretable load-pattern decomposition and clustering.
- The README references relevant scientific publications and clarifies DRPI terminology.
- The project can become a useful reproducible research artifact if demo data, tests, and DOI archiving are added.

## Weaknesses

### Documentation Gaps

- Before this documentation pass, the main entry point was Russian-first, limiting international discoverability.
- Screenshots are not yet committed.
- Demo mode is planned but not implemented.
- API behavior was only discoverable from code or Swagger at runtime.
- Method assumptions and equations were not separated into reviewer-friendly documents.
- Raspberry Pi deployment documentation exists but is currently Russian-language.

### Onboarding Issues

- New users need real Modbus hardware or a future demo workflow to see the dashboards populated.
- There is no automated setup script for demo data.
- There is no complete automated test suite.
- There is no CI workflow to validate importability, docs links, or method tests.
- The web app and pipeline run as separate processes, but no packaged process manager setup is provided for both together.

### Discoverability Issues

- GitHub topics must be set manually by the repository owner.
- No release has been created yet.
- No DOI is attached yet.
- No social preview image or screenshot gallery exists yet.
- No issue templates or pull request template are present yet.

## Recommendations

### GitHub Visibility

- Add the recommended topics from `docs/GITHUB_VISIBILITY.md`.
- Add a concise GitHub About description.
- Add screenshots generated from public-safe demo or anonymized data.
- Add a social preview image.
- Create a first release tagged `v0.1.0`.
- Add badges only after backing services exist, such as release, DOI, CI, or documentation status.

### Scientific Dissemination

- Connect the repository to Zenodo before or immediately after the first public release.
- Add DOI metadata to `CITATION.cff` once available.
- Add ORCID identifiers for authors if available.
- Publish or generate synthetic demo data to support reproducibility.
- Keep method documentation versioned with software releases.
- Cite the software release in papers, not only the GitHub branch.

### Community Building

- Enable GitHub Discussions for deployment questions and research-method discussion.
- Add issue templates for bug reports, documentation requests, and research questions.
- Label issues by area: `modbus`, `sqlite`, `api`, `dashboard`, `drpi`, `ssa`, `docs`, `deployment`, `research`.
- Mark beginner-friendly issues only when they can be completed without private hardware access.
- Document contribution expectations in pull request templates.

### Future Releases

- Add smoke tests and CI before `v0.2.0`.
- Implement demo mode or synthetic database generation.
- Persist SSA runs if the project needs strict research reproducibility.
- Add database migration strategy before schema changes become common.
- Consider Docker Compose or a documented two-service `systemd` deployment.
- Add English Raspberry Pi deployment documentation.

## Release Readiness Assessment

PowerMeter is suitable for a `v0.1.0` research prototype release after manual repository-owner actions are completed:

- add GitHub topics;
- add screenshots;
- create the GitHub release;
- enable Zenodo archiving;
- verify no private configuration or runtime data is committed.

It should not be presented as production-certified energy management software. It should be presented as open-source research software and a practical prototype for local industrial energy monitoring and demand-response analytics.
