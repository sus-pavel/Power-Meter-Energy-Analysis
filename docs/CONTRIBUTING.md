# Contributing

Thank you for considering a contribution to PowerMeter. The project combines field data acquisition, local storage, web dashboards, and research analytics, so contributions should be careful, reproducible, and well documented.

## Contribution Areas

Useful contributions include:

- documentation improvements;
- examples for Modbus meter configuration;
- tests for DRPI, SSA, aggregation, and Modbus decoding;
- dashboard usability improvements;
- deployment guides;
- demo-mode design or implementation;
- research validation and reproducibility materials.

## Before Opening an Issue

Check whether the issue is related to:

- device/register configuration;
- Modbus address offset;
- holding vs input registers;
- data type or word order;
- missing SQLite data;
- dashboard query period;
- unsupported aggregation interval.

For Modbus problems, run:

```bash
python -m services.debug_collector
```

This diagnostic tool checks offsets, function codes, raw registers, and decoding candidates without writing to the database.

## Issue Reports

Please include:

- operating system and Python version;
- PowerMeter version or commit hash;
- whether the issue occurs in the pipeline, web app, or both;
- relevant command;
- sanitized configuration snippet;
- sanitized logs or traceback;
- expected behavior;
- actual behavior.

Do not include real industrial network addresses, credentials, private site names, or confidential process data.

## Pull Request Process

1. Open an issue or discussion for large changes.
2. Keep the pull request focused on one concern.
3. Do not mix documentation, formatting, and behavior changes unless they are tightly related.
4. Preserve existing runtime behavior unless the PR explicitly proposes a behavior change.
5. Update documentation when configuration, endpoints, algorithms, or deployment steps change.
6. Add tests when changing calculation logic, parsing, database schema, or API response behavior.
7. Explain validation steps in the pull request description.

## Coding Standards

- Use clear Python type hints where they improve readability.
- Keep service responsibilities separated:
  - collector reads Modbus;
  - writer persists raw data;
  - aggregator builds time windows;
  - DRPI service orchestrates DRPI calculation;
  - core modules contain calculation logic;
  - web routes expose dashboard/API behavior.
- Prefer existing configuration patterns in `config/*.yaml`.
- Avoid hard-coding private device addresses or site-specific register maps.
- Keep comments focused on non-obvious engineering decisions.
- Keep public documentation in professional English unless the file is explicitly Russian-language documentation.

## Documentation Standards

When adding or changing docs:

- use concise headings;
- include commands that can be copied safely;
- distinguish implemented features from planned features;
- cite scientific methods and assumptions;
- keep screenshots and examples free of sensitive operational data.

## Testing

The repository does not yet include a complete automated test suite. Until it does, contributors should provide manual validation steps and, when practical, add small focused tests for:

- register decoding;
- address conversion;
- aggregation window naming and boundaries;
- DRPI edge cases;
- SSA decomposition on synthetic series;
- API response models.

## Security and Privacy

Never commit:

- real `config/devices.yaml` files;
- credentials;
- private IP maps;
- production SQLite databases;
- raw confidential load data;
- screenshots that reveal sensitive site details.

Use `config/devices.example.yaml` as the public template.

## Scientific Changes

Changes to DRPI, SSA, NILM-related logic, or evaluation methodology should include:

- method description;
- assumptions;
- parameter defaults;
- expected impact on previous results;
- references when applicable.
