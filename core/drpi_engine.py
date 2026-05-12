"""
core/drpi_engine.py

Назначение:
- расчёт DRPI по временным рядам активной мощности;
- поддержка расчёта rolling DRPI по окну фиксированной длины;
- адаптация логики старого DRFI-движка под 5-минутные данные.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass(slots=True)
class DRPIPoint:
    time: pd.Timestamp
    f1: float
    f2: float
    f3: float
    drpi: float
    r_raw: float


class DRPIEngine:
    def __init__(
        self,
        q_baseline: float = 0.2,
        flexible_share_target: float = 0.5,
        w1: float = 0.5,
        w2: float = 0.3,
        w3: float = 0.2,
    ):
        self.q_baseline = q_baseline
        self.flexible_share_target = flexible_share_target

        w_sum = w1 + w2 + w3
        self.w1 = w1 / w_sum
        self.w2 = w2 / w_sum
        self.w3 = w3 / w_sum

    def compute_drpi_rolling(
        self,
        ts: pd.Series,
        window_size: int = 288,
    ) -> pd.DataFrame:
        """
        Рассчитывает rolling DRPI по временному ряду активной мощности.

        Вход:
        - pd.Series
        - индекс: datetime-like
        - значения: active_power_avg

        Выход:
        - DataFrame с колонками:
          F1, F2, F3, R_raw, DRPI
        """
        ts = pd.Series(ts).astype(float).copy().sort_index()
        ts.index = pd.to_datetime(ts.index)

        values = ts.values
        index = ts.index
        rows = []

        if len(values) < window_size:
            return pd.DataFrame(columns=["F1", "F2", "F3", "R_raw", "DRPI"])

        for end_idx in range(window_size - 1, len(values)):
            start_idx = end_idx - window_size + 1
            p = values[start_idx:end_idx + 1]
            t_window = index[start_idx:end_idx + 1]

            if np.isnan(p).any():
                continue

            n = len(p)
            baseline = np.quantile(p, self.q_baseline)
            flex = np.maximum(0.0, p - baseline)

            e_tot = p.sum()
            e_flex = flex.sum()

            if e_tot <= 0 or e_flex <= 0:
                f1 = 0.0
                f2 = 0.0
            else:
                f1 = e_flex / e_tot

                idx_sorted = np.argsort(flex)[::-1]
                flex_sorted = flex[idx_sorted]
                cum = np.cumsum(flex_sorted)
                threshold = self.flexible_share_target * e_flex
                k = np.searchsorted(cum, threshold) + 1

                f2 = 1.0 - k / float(n)
                f2 = max(0.0, min(1.0, f2))

            p_max = p.max()
            r_raw = 0.0 if p_max <= 0 else float(np.mean(np.abs(np.diff(p)) / (p_max + 1e-9)))

            rows.append(
                {
                    "time": t_window[-1],
                    "F1": float(f1),
                    "F2": float(f2),
                    "R_raw": float(r_raw),
                }
            )

        df = pd.DataFrame(rows).set_index("time").sort_index()

        if df.empty:
            return pd.DataFrame(columns=["F1", "F2", "F3", "R_raw", "DRPI"])

        r_min, r_max = df["R_raw"].min(), df["R_raw"].max()
        if np.isclose(r_max - r_min, 0):
            df["F3"] = 0.5
        else:
            df["F3"] = (df["R_raw"] - r_min) / (r_max - r_min)

        df["DRPI"] = (
            self.w1 * df["F1"]
            + self.w2 * df["F2"]
            + self.w3 * df["F3"]
        )

        return df[["F1", "F2", "F3", "R_raw", "DRPI"]]