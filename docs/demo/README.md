# PowerMeter Demo Data

This directory is reserved for documentation-only sample data used to capture README screenshots.

Generate the fixture database with:

```bash
python scripts/seed_demo_data.py
```

The default output is:

```text
docs/demo/powermeter_demo.sqlite
```

The fixture uses fake device names, documentation-safe IP ranges (`192.0.2.0/24`, `198.51.100.0/24`, and `203.0.113.0/24`), deterministic timestamps, and a local demo login:

```text
admin / demo-admin
```

Do not use this database for real operations. To run the backend against the fixture for screenshots, explicitly point `POWERMETER_DB_PATH` at the generated file.
