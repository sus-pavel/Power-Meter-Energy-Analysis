# User Guide

PowerMeter App is a local macOS desktop application for monitoring Modbus TCP power meters and reviewing energy analytics.

## First Launch

Build and open `PowerMeter.app`. The desktop startup page checks the local backend at `http://127.0.0.1:8765`, then loads the main app after health succeeds.

Default beta credentials are:

```text
admin / admin
```

Change the password before using the app on a shared machine or real operational network.

## Main Workflow

1. Open Discovery and scan a trusted local network range.
2. Probe candidates to confirm they look like supported Modbus TCP devices.
3. Promote verified candidates into managed devices.
4. Start polling for managed devices.
5. Review live dashboard status and recent measurements.
6. Use History for trends.
7. Use DRPI for demand-response potential assessment.
8. Use SSA for time-series decomposition.

## Local Data

The desktop app stores runtime data here:

```text
~/Library/Application Support/PowerMeter/
```

Important files and directories:

- `app.sqlite` - local SQLite database.
- `logs/backend.log` - backend runtime log.
- `logs/desktop.log` - desktop supervisor log.
- `exports/`, `reports/`, `cache/`, `tmp/` - reserved local app directories.

## Boundaries

PowerMeter does not send data to a cloud service. It does not issue SCADA control commands. Modbus register maps may still need manual validation for specific meter models.
