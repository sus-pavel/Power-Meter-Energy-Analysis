# Singular Spectrum Analysis Method

PowerMeter uses Singular Spectrum Analysis (SSA) to decompose aggregated active-power time series into interpretable reconstructed components. The implementation is in `core/ssa_engine.py`, and the dashboard/API integration is in `web/routes/ssa.py` and `web/db.py`.

## Purpose

SSA helps identify structural patterns in electrical load profiles:

- slow trend components;
- daily or shift-related cycles;
- repeated operational patterns;
- higher-frequency variations;
- groups of components that may represent meaningful load behavior.

In PowerMeter, SSA is used as an analytical layer for load pattern research and demand-response interpretation.

## Input Data

The SSA dashboard analyzes aggregated `active_power_avg` data. Users can choose:

- one or more meters;
- start and end datetime;
- aggregation interval: 5, 10, 15, 30, or 60 minutes;
- SSA window length in points;
- maximum component count;
- KMeans cluster count.

When multiple meters are selected, the analysis series is the sum of meters at timestamps where all selected meters have data.

## Decomposition Workflow

### 1. Prepare the Time Series

The selected active-power series is sorted by timestamp and converted to numeric values.

If the selected time range has too few samples, the API returns a validation error.

### 2. Build the Trajectory Matrix

For a time series of length `N` and window length `L`, the number of lagged columns is:

```text
K = N - L + 1
```

The trajectory matrix `X` has shape `L x K` and is built from overlapping lagged fragments of the time series.

### 3. Singular Value Decomposition

The trajectory matrix is decomposed with SVD:

```text
X = U * Sigma * Vt
```

The implementation creates elementary matrices:

```text
X_i = Sigma_i * outer(U_i, Vt_i)
```

The sum of elementary matrices is checked against the original trajectory matrix.

### 4. Reconstruct Elementary Components

Each elementary matrix is converted back to a time series by diagonal averaging. The reconstructed component series are returned as `RC1`, `RC2`, and so on.

### 5. Calculate Contribution

Component contribution is calculated from squared singular values:

```text
contribution_i = Sigma_i^2 / sum(Sigma^2)
```

The dashboard returns cumulative contribution so users can estimate how many components explain most of the signal structure.

### 6. Calculate W-Correlation

W-correlation measures similarity between reconstructed components using SSA weights. It helps identify components that may belong to the same oscillatory mode or pattern family.

### 7. Extract Amplitude-Frequency Features

For each selected component, the implementation extracts two features:

- dominant frequency from the power spectral density of a Hanning-windowed component;
- amplitude as the component standard deviation.

The frequency search uses positive frequencies below the Nyquist limit.

### 8. Cluster Components

Components are clustered with KMeans in the two-dimensional feature space:

```text
(dominant_frequency, amplitude)
```

The trend component can be excluded from clustering. The current interactive SSA API excludes component `0` as trend and separately returns it in grouped output.

### 9. Reconstruct Cluster Series

For each cluster, the implementation sums reconstructed components assigned to that cluster. The dashboard returns:

- original series;
- trend;
- reconstructed cluster series;
- elementary component series;
- amplitude-frequency scatter points;
- W-correlation matrix.

## Default Parameters

Web API defaults:

| Parameter | Default | Meaning |
| --- | --- | --- |
| `aggregation_min` | `30` | Aggregation interval in minutes. |
| `window_points` | `48` | SSA window length. At 30-minute aggregation, this equals one day. |
| `component_count` | `20` | Maximum number of components exposed in the response. |
| `cluster_count` | `4` | Requested number of KMeans clusters. |

Configuration defaults in `config/ssa.yaml`:

| Key | Default | Meaning |
| --- | --- | --- |
| `agg_table_name` | `agg_30min` | Default source table for SSA service configuration. |
| `history_points` | `336` | Seven days at 48 points per day. |
| `window_length` | `48` | One day at 30-minute resolution. |
| `fs` | `48` | Sampling frequency for spectral features at 30-minute resolution. |
| `n_clusters` | `3` | Default cluster count in service configuration. |
| `max_components` | `30` | Maximum components considered. |
| `trend_component` | `0` | Component excluded as trend. |

## Practical Usage

Recommended workflow:

1. Start with 30-minute aggregation and a 7-day period.
2. Use `window_points = 48` to capture daily structure.
3. Inspect cumulative contribution to identify dominant components.
4. Use W-correlation to find component groups that may represent paired oscillatory behavior.
5. Inspect amplitude-frequency clusters to distinguish trend-like, daily, and high-frequency components.
6. Compare cluster reconstructions with known operational schedules.
7. Use reconstructed components as explanatory signals for demand-response potential analysis.

## Limitations

- SSA is descriptive and exploratory; it does not identify physical equipment by itself.
- Component interpretation depends on the aggregation interval and selected window length.
- KMeans cluster labels are not semantic labels; they require domain interpretation.
- Missing data can reduce the usable time range, especially when summing multiple meters.
- The current dashboard computes SSA on demand and does not persist SSA runs.

## Scientific Context

The SSA block follows the methodology of electrical load decomposition research: transform the time series into a trajectory matrix, decompose it using SVD, reconstruct components, and group them by frequency-amplitude behavior. This supports load-pattern classification, quasi-dynamic operating-mode analysis, and research into demand-response flexibility.
