# App Stage 5: Analytics and Trends

Stage 5 finalizes the application data pipeline after polling writes raw measurements.

## Data Flow

```text
measurements_raw
→ measurements_agg_5min
→ measurements_agg_10min
→ measurements_agg_15min
→ measurements_agg_30min
→ measurements_agg_1h
→ app_drpi_results
→ trends, DRPI, SSA APIs
→ React analytics UI
```

## Tables

Aggregation tables:

- `measurements_agg_5min`
- `measurements_agg_10min`
- `measurements_agg_15min`
- `measurements_agg_30min`
- `measurements_agg_1h`

Each table stores completed windows by `device_id`, `metric`, and `unit`, with mean, min, max, and sample count. Windows are unique by `window_start`, `window_end`, `device_id`, and `metric`.

DRPI table:

- `app_drpi_results`

## Background Services

Started on backend startup:

- aggregation service;
- DRPI service;
- retention service.

Shutdown cancels sleeping service tasks so the app process can stop cleanly for future desktop packaging.

## Aggregation Logic

The app aggregation service follows the prototype aggregator pattern:

- reads raw measurements;
- processes only completed time windows;
- writes idempotently with unique constraints;
- leaves raw polling intact.

Unlike the research prototype, the app service aggregates every metric present in `measurements_raw`.

## DRPI Integration

DRPI uses the prototype `DRPIEngine` logic unchanged:

- `F1`
- `F2`
- `F3`
- `R_raw`
- `DRPI`

The app service adapts `measurements_agg_5min` into the same pandas series format expected by the prototype engine. The default metric is configurable with `POWERMETER_ANALYTICS_METRIC` and defaults to `active_power_total`.

## SSA Integration

SSA uses the prototype implementation unchanged:

- trajectory matrix;
- SVD;
- elementary component reconstruction;
- W-correlation;
- KMeans clustering by dominant frequency and amplitude.

The app service loads app aggregate data, sums selected devices when multiple devices are selected, and returns chart-ready original, trend, component, cluster, W-correlation, contribution, and amplitude/frequency data.

## APIs

Trends:

- `GET /api/trends/series`
- `GET /api/trends/summary`
- `GET /api/trends/metrics`

DRPI:

- `GET /api/drpi/summary`
- `GET /api/drpi/history`
- `GET /api/drpi/components`
- `POST /api/drpi/recalculate`

SSA:

- `POST /api/ssa/analyze`

## Frontend Pages

- `/history`
- `/drpi`
- `/ssa`

The UI uses compact engineering-oriented controls and lightweight SVG chart components. It avoids a heavy charting dependency for now.

## Limitations

- No export or reporting.
- No PDF generation.
- No alerting.
- No cloud sync.
- No desktop packaging.
- Retention policy is simple age-based deletion.

## Stage 6 Preparation

Stage 5 keeps database paths configurable, allows the frontend API base URL to be set through `VITE_API_BASE_URL`, and runs the backend as one app process with background services under FastAPI startup/shutdown.
