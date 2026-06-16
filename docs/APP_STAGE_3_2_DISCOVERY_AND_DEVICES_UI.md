# App Stage 3.2: Discovery And Device Management UI

Stage 3.2 exposes the first full operational workflow in the PowerMeter UI: discovery scan management, candidate review, register probing, promotion, device viewing/editing, and register map maintenance.

## Routes

- `/discovery`: discovery job list grouped by active, completed, cancelled, and failed.
- `/discovery/jobs/:jobId`: discovery job progress and result rows.
- `/candidates`: candidate inbox with status filters and IP/unit search.
- `/candidates/:candidateId`: candidate metadata, fingerprint, probe results, probe action, promotion, and rejection.
- `/devices`: managed device table.
- `/devices/:deviceId`: device details and register map editor.

## Workflows

Discovery:

1. Open `/discovery`.
2. Start a scan with Start IP and End IP.
3. UI validates IPv4 order and limits scans to 1024 hosts.
4. Running jobs refresh every 5 seconds.
5. Jobs can be cancelled by admin or chief engineer.

Candidate review:

1. Open `/candidates`.
2. Filter by all, discovered, reviewed, promoted, or rejected.
3. Open a candidate details page.
4. Run safe probe.
5. Review fingerprint and probe result table.
6. Promote or reject candidate.

Promotion:

1. Click Promote Device on a candidate.
2. Enter device name, location, and description.
3. Backend creates a managed device and register map from valid probe results.
4. UI navigates to `/devices/:deviceId`.

Device management:

1. Open `/devices`.
2. View or delete devices.
3. Open device details.
4. Edit name, location, description, and enabled state.
5. Add, edit, delete, enable, or disable register map entries.

## Permissions

- `admin`: full device lifecycle access.
- `chief_engineer`: full device lifecycle access.
- `analyst`: read-only discovery, candidates, devices, and register maps.
- `guest`: no access to device lifecycle pages.

The UI hides restricted actions, and backend permissions remain authoritative.

## API Usage

Discovery:

- `GET /api/discovery/jobs`
- `POST /api/discovery/scan`
- `GET /api/discovery/jobs/{job_id}`
- `GET /api/discovery/jobs/{job_id}/results`
- `POST /api/discovery/jobs/{job_id}/cancel`

Candidates:

- `GET /api/candidates`
- `GET /api/candidates/{candidate_id}`
- `POST /api/candidates/{candidate_id}/probe`
- `POST /api/candidates/{candidate_id}/promote`
- `POST /api/candidates/{candidate_id}/reject`

Devices:

- `GET /api/devices`
- `GET /api/devices/{device_id}`
- `PUT /api/devices/{device_id}`
- `DELETE /api/devices/{device_id}`
- `GET /api/devices/{device_id}/registers`
- `POST /api/devices/{device_id}/registers`
- `PUT /api/devices/{device_id}/registers/{register_id}`
- `DELETE /api/devices/{device_id}/registers/{register_id}`

## Component Structure

- `DiscoveryJobTable`
- `DiscoveryProgressCard`
- `CandidateTable`
- `CandidateStatusBadge`
- `CandidateDetailsCard`
- `ProbeResultsTable`
- `DeviceTable`
- `DeviceDetailsCard`
- `RegisterMapTable`
- `ConfirmDialog`
- `PromotionDialog`

## Limitations

- No realtime charts.
- No historical analytics.
- No DRPI or SSA screens.
- No Tauri packaging.
- Discovery execution is intentionally conservative and backend-controlled.

## Next Stage

Stage 3.3 can add richer operational usability: scan result drilldowns, candidate bulk actions, better register validation, audit log views, and preparation for analytics navigation.
