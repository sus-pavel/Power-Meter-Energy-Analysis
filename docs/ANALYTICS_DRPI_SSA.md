# Analytics: DRPI and SSA

PowerMeter App includes analytics inherited from the research prototype and surfaced in the React UI.

## DRPI

DRPI is the Demand Response Potential Index. It estimates demand-response potential from active-power time series using the existing project methodology.

The app fork preserves the existing DRPI mathematical logic. Packaging and desktop work should not change formula behavior.

Use DRPI pages to inspect summary values, history, and component behavior after enough measurements and aggregates are available.

## SSA

SSA is Singular Spectrum Analysis for time-series decomposition. PowerMeter uses it to inspect load patterns and component structure in measured active-power data.

The app fork preserves the existing SSA decomposition logic for prototype compatibility.

## Data Requirements

Analytics depend on successful polling, measurement storage, and aggregation. Empty or sparse datasets may produce limited or unavailable results.

Method-level details remain in:

- [DRPI_METHOD.md](DRPI_METHOD.md)
- [SSA_METHOD.md](SSA_METHOD.md)
