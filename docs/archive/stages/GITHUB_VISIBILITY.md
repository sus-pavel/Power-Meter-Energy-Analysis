# GitHub Visibility Guide

This guide lists recommended GitHub settings and repository-presentation actions for PowerMeter.

## Repository Description

Recommended short description:

```text
Open-source Modbus TCP energy monitoring platform with real-time dashboards, demand-response analytics, and SSA load-pattern analysis.
```

## Recommended Topics

Add these topics in the GitHub repository settings:

```text
modbus-tcp
energy-monitoring
smart-meter
industrial-iot
demand-response
energy-flexibility
load-profiling
singular-spectrum-analysis
ssa
nilm
fastapi
sqlite
raspberry-pi
energy-analytics
```

These topics improve discovery by engineers searching for Modbus and monitoring projects, and by researchers searching for demand-response, flexibility, SSA, NILM, and load profiling tools.

## About Section

Recommended GitHub About settings:

- Description: use the short description above.
- Website: add a documentation page, project page, or release page when available.
- Topics: use the recommended list above.
- Include in the README: screenshots, quick start, architecture, citation, and license.

## Social Preview

Create a social preview image that includes:

- project name: `PowerMeter`;
- one-line positioning statement;
- a dashboard screenshot or clean architecture graphic;
- keywords: Modbus TCP, DRPI, SSA, FastAPI, SQLite.

Avoid screenshots that reveal private infrastructure, IP addresses, production values, or customer/site details.

## Release Strategy

Recommended release approach:

1. Prepare `v0.1.0` as the first public research prototype release.
2. Add release notes that match `docs/RELEASE_PLAN.md`.
3. Tag releases using semantic versioning:
   - `v0.1.x` for documentation fixes, bug fixes, and minor prototype improvements;
   - `v0.2.0` for demo mode, test suite, or API/data model improvements;
   - `v1.0.0` only after stable configuration, API, documentation, tests, and deployment path.
4. Archive releases with Zenodo after GitHub release creation.
5. Add DOI badges and citation links once Zenodo issues a DOI.

## README Badges

After repository workflows and DOI integration exist, consider adding badges for:

- license;
- latest release;
- Python version;
- DOI;
- documentation status;
- tests or CI status.

Do not add badges that are not backed by active services.

## Issue and Pull Request Templates

Recommended templates:

- bug report;
- feature request;
- documentation issue;
- research/methodology question;
- pull request checklist.

Each template should ask users to avoid sharing sensitive industrial data.

## Scientific Visibility

Recommended actions:

- Keep `CITATION.cff` valid and updated.
- Connect the repository to Zenodo.
- Add ORCID identifiers to `CITATION.cff` if available.
- Link publications from the README and method docs.
- Add reproducible examples or notebooks when public data is available.
- Publish demo data with clear provenance and license.
- Reference versioned releases in papers and presentations.

## Community Building

Useful GitHub features:

- Enable Discussions for research questions and deployment stories.
- Use Issues for actionable bugs and feature requests.
- Label issues by area: `modbus`, `database`, `api`, `dashboard`, `drpi`, `ssa`, `docs`, `deployment`, `research`.
- Mark beginner-friendly issues as `good first issue` only when they are well scoped and do not require private hardware access.

## Repository Hygiene Before Public Release

Before each release:

- confirm that `config/devices.yaml` is not committed;
- confirm that SQLite runtime databases are not committed;
- confirm screenshots do not expose sensitive details;
- run the diagnostic collector only against authorized devices;
- verify that README links and docs links resolve;
- update `CHANGELOG.md`;
- update `CITATION.cff` if version, title, authors, or DOI changed.
