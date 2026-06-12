# Demand Response Potential Index Method

The Demand Response Potential Index (DRPI) estimates how promising a load profile is for demand response participation. The implementation is in `core/drpi_engine.py`; production orchestration is in `services/drpi_service.py`.

## Purpose

DRPI is intended to support:

- comparison of flexibility potential across meters;
- tracking of flexibility changes over time;
- identification of periods where load reduction or shifting may be practical;
- research workflows that compare original and reconstructed load patterns.

The index is not a direct control signal. It is a screening and interpretation metric that should be combined with process constraints, operational schedules, and domain knowledge.

## Input Data

The production DRPI service uses:

- source table: `agg_5min`;
- metric: `active_power_avg`;
- default window size: `288` points;
- default physical duration: 24 hours at 5-minute resolution;
- source mode: `all_plus_total`, meaning individual meters and summed `TOTAL` consumption.

The service writes results to `drpi_results`.

## Notation

For one rolling window, let:

- `p_i` be active power at sample `i`;
- `n` be the number of samples in the window;
- `q` be the baseline quantile, default `0.2`;
- `target` be the flexible-share concentration target, default `0.5`.

The baseline is:

```text
b = quantile(p, q)
```

Flexible power above baseline is:

```text
flex_i = max(0, p_i - b)
```

Total and flexible energy proxies are:

```text
E_total = sum(p_i)
E_flex  = sum(flex_i)
```

Because the samples are evenly spaced, sums of power samples are proportional to energy over the window.

## Component F1: Flexible Load Share

`F1` estimates the share of consumption above the baseline:

```text
F1 = E_flex / E_total
```

If `E_total <= 0` or `E_flex <= 0`, the implementation sets `F1 = 0`.

Interpretation:

- higher `F1` means more load is above the low-load baseline;
- lower `F1` means the profile has less apparent flexible margin.

## Component F2: Temporal Concentration

`F2` estimates how concentrated the flexible load is in time.

The implementation sorts `flex_i` in descending order, calculates the cumulative sum, and finds the smallest `k` such that:

```text
sum_top_k(flex_i) >= target * E_flex
```

Then:

```text
F2 = 1 - k / n
```

The result is clipped to `[0, 1]`.

Interpretation:

- higher `F2` means a large share of flexible load is concentrated in fewer time steps;
- lower `F2` means flexible load is spread more evenly across the window.

## Component F3: Normalized Dynamics

The raw dynamics score is:

```text
R_raw = mean(abs(diff(p)) / (max(p) + 1e-9))
```

If `max(p) <= 0`, `R_raw = 0`.

After rolling windows are computed, `R_raw` is min-max normalized across the computed result set:

```text
F3 = (R_raw - min(R_raw)) / (max(R_raw) - min(R_raw))
```

If all `R_raw` values are effectively equal, the implementation sets:

```text
F3 = 0.5
```

Interpretation:

- higher `F3` indicates stronger short-term dynamics relative to the observed range;
- lower `F3` indicates a smoother profile within the observed range.

## Final DRPI

DRPI is a weighted sum:

```text
DRPI = w1 * F1 + w2 * F2 + w3 * F3
```

Default weights in `config/drpi.yaml`:

```text
w1 = 0.5
w2 = 0.3
w3 = 0.2
```

The engine normalizes the weights by their sum before calculation.

## Assumptions

- The active-power series is sufficiently sampled and time-aligned.
- The window is long enough to capture daily load variation.
- The low quantile is a practical baseline proxy for non-flexible consumption.
- Flexible potential is approximated from observed profile structure, not verified equipment-level controllability.
- Demand response feasibility depends on process, comfort, production, safety, and contractual constraints that are outside the current algorithm.

## Interpretation Guidelines

Use DRPI comparatively:

- compare sources within the same site;
- compare periods for the same source;
- compare original profiles with reconstructed SSA components;
- track whether flexibility potential is becoming more concentrated or more dynamic.

Avoid interpreting DRPI as:

- guaranteed curtailment capacity;
- a dispatch command;
- a substitute for equipment-level validation;
- a universal metric across sites without calibration.

## Implementation Notes

The current service inserts new DRPI rows incrementally. `F3` normalization is based on the calculation set available to the engine during a run. For strict reproducibility across releases, future versions should document or persist a fixed normalization policy.

## Configuration

Main configuration keys in `config/drpi.yaml`:

| Key | Default | Meaning |
| --- | --- | --- |
| `agg_table_name` | `agg_5min` | Input aggregation table. |
| `metric_name` | `active_power_avg` | Input metric. |
| `results_table_name` | `drpi_results` | Output table. |
| `source_mode` | `all_plus_total` | Calculate per meter, total, or both. |
| `window_size` | `288` | Rolling samples per calculation. |
| `q_baseline` | `0.2` | Baseline quantile. |
| `flexible_share_target` | `0.5` | Target share for temporal concentration. |
| `w1`, `w2`, `w3` | `0.5`, `0.3`, `0.2` | DRPI component weights. |

## Scientific Context

The method aligns with research on cluster-informed demand-response flexibility assessment for reconstructed load patterns. In this repository, the production index is named DRPI, while related earlier work may refer to a Demand Response Flexibility Index.
