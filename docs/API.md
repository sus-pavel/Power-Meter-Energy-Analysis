# API Documentation

PowerMeter exposes dashboard pages and JSON endpoints through FastAPI. Generated OpenAPI documentation is available at:

```text
http://localhost:8000/docs
```

Default local base URL:

```text
http://localhost:8000
```

## Dashboard Pages

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Redirects to `/overview`. |
| `GET` | `/overview` | Overview dashboard with current power, meter activity, DRPI summary, and heatmap. |
| `GET` | `/history` | Real-time and historical measurement trends. |
| `GET` | `/drpi` | DRPI dashboard for `TOTAL` or individual meters. |
| `GET` | `/ssa` | Interactive SSA analysis page. |

## Common Query Parameters

Several endpoints support these parameters:

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `mode` | string | `online` | Either `online` or `historical`. |
| `year` | integer | `null` | Historical year filter. |
| `month` | integer | `null` | Historical month filter. |
| `day` | integer | `null` | Historical day filter, used by history series. |
| `source_id` | string | `TOTAL` | DRPI source, either `TOTAL` or a meter identifier. |
| `aggregation_min` | integer | endpoint-specific | Aggregation interval in minutes: `5`, `10`, `15`, `30`, or `60`. |

Timestamps in JSON responses are Unix timestamps in seconds.

## History API

### `GET /api/history/realtime`

Returns current meter cards for the latest raw measurements. The response includes metric snapshots, min/max values over the recent horizon, sparklines, last timestamp, and source status.

Example:

```bash
curl "http://localhost:8000/api/history/realtime"
```

### `GET /api/history/series`

Returns chart series for active power, current, voltage, and frequency.

Parameters:

- `mode`: `online` or `historical`.
- `year`: required for historical mode.
- `month`: required for historical mode.
- `day`: required for historical mode.
- `aggregation_min`: `5`, `10`, `15`, `30`, or `60`; used in historical mode.

Examples:

```bash
curl "http://localhost:8000/api/history/series?mode=online"
curl "http://localhost:8000/api/history/series?mode=historical&year=2026&month=6&day=12&aggregation_min=5"
```

## Overview API

### `GET /api/overview/summary`

Returns the current DRPI, current total active power, active/total meter count, DRPI sparkline, total-power sparkline, and reference timestamp.

Example:

```bash
curl "http://localhost:8000/api/overview/summary?mode=online"
```

### `GET /api/overview/power-meters`

Returns active-power time series for individual power meters.

Example:

```bash
curl "http://localhost:8000/api/overview/power-meters?mode=historical&year=2026&month=6"
```

### `GET /api/overview/drpi-heatmap`

Returns weekday/hour heatmap cells for DRPI values.

Parameters:

- `source_id`: defaults to `TOTAL`.
- `mode`: `online` or `historical`.
- `year`, `month`: optional historical filters.

Example:

```bash
curl "http://localhost:8000/api/overview/drpi-heatmap?source_id=TOTAL&mode=online"
```

## DRPI API

### `GET /api/drpi/summary`

Returns current DRPI, preferred days, 24-hour minimum/maximum, current component values, component sparklines, and reference timestamp.

Example:

```bash
curl "http://localhost:8000/api/drpi/summary?source_id=TOTAL&mode=online"
```

### `GET /api/drpi/history`

Returns DRPI time series for a source.

Example:

```bash
curl "http://localhost:8000/api/drpi/history?source_id=PowerMeter_1&mode=historical&year=2026&month=6"
```

### `GET /api/drpi/components`

Returns time series for `F1`, `F2`, and `F3`.

Example:

```bash
curl "http://localhost:8000/api/drpi/components?source_id=TOTAL&mode=online"
```

## SSA API

### `GET /api/ssa/analyze`

Runs SSA analysis for selected meter(s) over an aggregated active-power time range.

Parameters:

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `device_ids` | repeated string | yes | none | One or more meter identifiers. Repeated query parameters are supported. |
| `start_at` | string | yes | none | Local datetime in `YYYY-MM-DDTHH:MM` format. |
| `end_at` | string | yes | none | Local datetime in `YYYY-MM-DDTHH:MM` format. |
| `aggregation_min` | integer | no | `30` | Aggregation interval: `5`, `10`, `15`, `30`, or `60`. |
| `window_points` | integer | no | `48` | SSA trajectory window length in samples. |
| `component_count` | integer | no | `20` | Maximum number of components included in response and clustering. |
| `cluster_count` | integer | no | `4` | Requested KMeans cluster count. |

Example for one meter:

```bash
curl "http://localhost:8000/api/ssa/analyze?device_ids=PowerMeter_1&start_at=2026-06-01T00:00&end_at=2026-06-07T23:30&aggregation_min=30&window_points=48&component_count=20&cluster_count=4"
```

Example for a summed group of meters:

```bash
curl "http://localhost:8000/api/ssa/analyze?device_ids=PowerMeter_1&device_ids=PowerMeter_2&start_at=2026-06-01T00:00&end_at=2026-06-07T23:30"
```

Response sections:

- `summary`: selected period, aggregation, SSA settings, sample count, and sampling frequency.
- `original_series`: original aggregated active-power time series.
- `wcorr`: W-correlation matrix for reconstructed components.
- `cumulative_contribution`: cumulative singular-value contribution by component.
- `amplitude_frequency`: component scatter data with cluster assignment.
- `grouped_series`: original series, trend, and cluster reconstructions.
- `component_series`: reconstructed elementary components.
- `cluster_series`: reconstructed sums by cluster.

Errors:

- `400` when dates are invalid, the aggregation interval is unsupported, meters are missing, or there are insufficient complete points for analysis.

## Response Models

The canonical response model definitions are in `web/schemas.py`. The generated `/docs` page should be treated as the authoritative machine-readable API contract for the currently running code.
