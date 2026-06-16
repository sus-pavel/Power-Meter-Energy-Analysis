# App Stage 2.1: Safe Modbus TCP Device Discovery

Stage 2.1 adds a conservative discovery subsystem for possible Modbus TCP endpoints. It does not identify devices, probe full register maps, or promote devices automatically.

## Architecture

Discovery lives inside the application backend:

- API router: `backend/app/api/discovery.py`
- scan service and runtime: `backend/app/services/discovery_service.py`
- schemas: `backend/app/schemas/discovery.py`
- database tables: `scan_jobs`, `scan_results`

The scanner runs as an asyncio background task in the FastAPI process. It uses bounded concurrency with at most 20 hosts being checked at once.

## Workflow

1. A user creates a scan job with `ip_start` and `ip_end`.
2. The backend validates the IPv4 range.
3. A `scan_jobs` row is created with `pending` status.
4. A background scan starts and marks the job `running`.
5. Each host is checked on TCP port `502` with a 1000 ms timeout.
6. If the port is open, the scanner sends a minimal read-only Modbus TCP request.
7. Only unit IDs `1`, `2`, `3`, `10`, `100`, and `247` are checked.
8. Results are stored in `scan_results`.
9. The job finishes as `completed`, `failed`, or `cancelled`.

## Permissions

- `admin`: create scans, cancel scans, view jobs and results.
- `chief_engineer`: create scans, cancel scans, view jobs and results.
- `analyst`: view jobs and results only.
- `guest`: no discovery access.

## API Examples

Create a scan:

```bash
curl -X POST http://127.0.0.1:8000/api/discovery/scan \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"ip_start":"192.168.1.1","ip_end":"192.168.1.254"}'
```

List jobs:

```bash
curl -H "Authorization: Bearer <token>" \
  http://127.0.0.1:8000/api/discovery/jobs
```

Check job status:

```bash
curl -H "Authorization: Bearer <token>" \
  http://127.0.0.1:8000/api/discovery/jobs/1
```

Read results:

```bash
curl -H "Authorization: Bearer <token>" \
  http://127.0.0.1:8000/api/discovery/jobs/1/results
```

Cancel a scan:

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://127.0.0.1:8000/api/discovery/jobs/1/cancel
```

## Limitations

- Discovery only supports IPv4 ranges.
- Port `502` is fixed for this stage.
- The scanner does not identify vendors, models, or meter types.
- The scanner does not perform broad register probing.
- An open TCP port is not treated as a power meter.
- A Modbus response is only treated as a Modbus-compatible candidate endpoint.
- Running jobs are process-local; if the backend stops, unfinished jobs are marked failed on next startup.

## Security And Safety

- All Modbus operations are read-only.
- No write functions are sent.
- The scanner uses short timeouts and bounded concurrency.
- Unit ID discovery is limited to `1`, `2`, `3`, `10`, `100`, and `247`.
- Large ranges are capped by `POWERMETER_DISCOVERY_MAX_HOSTS`, defaulting to 4096 hosts.
- Use scans only on networks you administer or have explicit permission to test.

## Stage 2.2 Preparation

The stored scan results include TCP status, Modbus response status, response timing, and candidate unit IDs. Stage 2.2 can build on this to add device fingerprinting, safe register probing, templates, and promotion into managed devices without replacing the scan job schema.
