# App Stage 2.2: Probe, Fingerprint, And Promotion

Stage 2.2 turns Modbus-compatible scan results into reviewable candidates that can be safely probed and promoted into managed PowerMeter devices.

## Architecture

- Candidate API: `backend/app/api/candidates.py`
- Candidate persistence: `backend/app/services/candidate_service.py`
- Register probe engine: `backend/app/services/register_probe_service.py`
- Fingerprinting: `backend/app/services/fingerprint_service.py`
- Probe profiles: `backend/app/config/probe_profiles.yaml`

Discovery remains separate. A scan result that includes responding unit IDs automatically creates one `discovered_candidates` row per unit ID.

## Candidate Lifecycle

```text
Discovery Scan
→ Scan Result
→ Candidate: discovered
→ Register Probe
→ Candidate: reviewed
→ Promote or Reject
→ Managed Device or rejected candidate
```

Statuses:

- `discovered`: created automatically from a responding scan result.
- `reviewed`: probe and fingerprint have run.
- `promoted`: converted into a managed device.
- `rejected`: explicitly dismissed by an authorized user.

## Fingerprinting Strategy

Fingerprinting is intentionally broad and conservative. The app estimates only a probable class:

- `power_meter`
- `power_quality_meter`
- `energy_analyzer`
- `plc`
- `industrial_controller`
- `unknown_modbus_device`

No vendor-specific identification or reverse engineering is attempted. Vendor is reported as `unknown` for this stage.

## Probe Profiles

Profiles live in `backend/app/config/probe_profiles.yaml`.

The default `generic_energy_meter` profile reads a small configured set of holding and input registers and tries `float32` and `float32_swapped`. Operators can adjust this file without changing Python code.

## Promotion Workflow

Promotion creates:

- one row in `devices`;
- one `device_registers` row for each valid probe result.

Only probe results where `valid = true` are promoted into the register map.

## API

- `GET /api/candidates`
- `GET /api/candidates/{candidate_id}`
- `POST /api/candidates/{candidate_id}/probe`
- `POST /api/candidates/{candidate_id}/promote`
- `POST /api/candidates/{candidate_id}/reject`

Promotion request:

```json
{
  "device_name": "Main Switchboard Meter",
  "location": "MDB Room"
}
```

## Permissions

- `admin`: view, probe, promote, reject.
- `chief_engineer`: view, probe, promote, reject.
- `analyst`: view only.
- `guest`: no access.

## Safety Limits

- Read-only Modbus operations only.
- No writes.
- No address sweeps.
- No bulk scans.
- Timeout-protected reads.
- Small configurable register profile.
- Short delay between register reads.
- Results are candidates, not proof of device identity.

## Limitations

- Fingerprinting is heuristic and intentionally approximate.
- Vendor detection is not implemented.
- Register semantics are not inferred beyond generated probe metric names.
- Promotion creates a starter register map that should be reviewed by a human.

## Before Stage 3 UI

The backend now exposes scan jobs, candidates, probe, promote, and reject endpoints. Stage 3 can build the UI directly on these APIs: candidate inbox, probe review, promotion form, and managed device register editor.
