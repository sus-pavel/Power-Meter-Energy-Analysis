"""
core/ssa_engine.py

Назначение:
- выполнять SSA-декомпозицию временного ряда;
- реконструировать элементарные компоненты;
- кластеризовать компоненты методом KMeans по исходной логике:
    1) доминирующая частота
    2) амплитуда
- возвращать суммы реконструированных компонент по кластерам.

Порядок расчёта соответствует исходной реализации проекта:
SSADecomposer -> reconstruct elementary components -> feature extraction
(freq, amplitude) -> KMeans -> sum components inside each cluster
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


@dataclass(slots=True)
class SSAResult:
    ts: np.ndarray
    dates: pd.Index
    L: int
    K: int
    X: np.ndarray
    X_elem: np.ndarray
    Sigma: np.ndarray
    contribution: np.ndarray
    cumulative_contribution: np.ndarray
    wcorr: np.ndarray


@dataclass(slots=True)
class SSAKMeansResult:
    df_anal: pd.DataFrame
    cluster_stats: pd.DataFrame
    reconstructed: dict[int, np.ndarray]
    labels: np.ndarray
    singular_values: np.ndarray
    contribution: np.ndarray
    cumulative_contribution: np.ndarray


class SSADecomposer:
    """
    SSA decomposition core preserving the original project logic.

    Preserved names:
    - ts
    - dates
    - L
    - K
    - X
    - X_elem
    - Sigma
    """

    def __init__(self, time_series, window_size: int):
        if isinstance(time_series, pd.Series):
            self.ts = time_series.astype(float).values
            self.dates = time_series.index
        else:
            arr = np.asarray(time_series, dtype=float)
            self.ts = arr
            self.dates = pd.RangeIndex(len(arr))

        self.L = int(window_size)
        if self.L < 2:
            raise ValueError("window_size must be >= 2")
        if self.L >= len(self.ts):
            raise ValueError("window_size must be smaller than the series length")

        self.K = len(self.ts) - self.L + 1
        self.X: Optional[np.ndarray] = None
        self.X_elem: Optional[np.ndarray] = None
        self.Sigma: Optional[np.ndarray] = None

    def create_trajectory_matrix(self) -> np.ndarray:
        self.X = np.column_stack([self.ts[i:i + self.L] for i in range(self.K)])
        return self.X

    def svd_decomposition(self) -> tuple[np.ndarray, np.ndarray]:
        if self.X is None:
            self.create_trajectory_matrix()

        U, Sigma, Vt = np.linalg.svd(self.X, full_matrices=False)
        self.Sigma = Sigma
        self.X_elem = np.array(
            [Sigma[i] * np.outer(U[:, i], Vt[i, :]) for i in range(len(Sigma))]
        )

        if not np.allclose(self.X, self.X_elem.sum(axis=0), atol=1e-5):
            raise ValueError("Sum of elementary matrices is not equal to the trajectory matrix.")

        return self.X_elem, self.Sigma

    def contribution_table(self) -> pd.DataFrame:
        if self.Sigma is None:
            self.svd_decomposition()

        sigma_sumsq = float((self.Sigma ** 2).sum())
        rel = (self.Sigma ** 2) / sigma_sumsq
        cum = np.cumsum(rel)

        return pd.DataFrame(
            {
                "component": np.arange(len(self.Sigma)),
                "contribution": rel,
                "cumulative_contribution": cum,
            }
        )

    def compute_wcorr(self) -> np.ndarray:
        if self.X_elem is None:
            self.svd_decomposition()

        N = self.L + self.K - 1
        w = np.array([min(i + 1, self.L, N - i) for i in range(N)], dtype=float)
        F_elem = np.array([self._x_to_ts(X_i) for X_i in self.X_elem])

        weighted_squares = F_elem ** 2 * w
        norms = np.sqrt(np.sum(weighted_squares, axis=1))
        norms[norms == 0] = 1e-10

        F_weighted = F_elem * np.sqrt(w)
        wcorr = np.abs(F_weighted @ F_weighted.T / np.outer(norms, norms))
        np.fill_diagonal(wcorr, 1.0)
        return wcorr

    def reconstruct_component(self, component_id: int) -> np.ndarray:
        if self.X_elem is None:
            self.svd_decomposition()
        return self._x_to_ts(self.X_elem[component_id])

    def reconstruct_components(self, component_ids: list[int] | np.ndarray) -> np.ndarray:
        comp_ids = np.asarray(component_ids, dtype=int)
        if comp_ids.size == 0:
            return np.zeros(len(self.ts))
        return np.sum([self.reconstruct_component(i) for i in comp_ids], axis=0)

    def grouped_components(self, groups: dict[str, list[int]]) -> pd.DataFrame:
        data = {}
        for name, component_ids in groups.items():
            data[name] = self.reconstruct_components(component_ids)
        return pd.DataFrame(data, index=self.dates)

    def fit(self) -> SSAResult:
        self.create_trajectory_matrix()
        self.svd_decomposition()
        wcorr = self.compute_wcorr()
        contr = self.contribution_table()

        return SSAResult(
            ts=self.ts,
            dates=self.dates,
            L=self.L,
            K=self.K,
            X=self.X,
            X_elem=self.X_elem,
            Sigma=self.Sigma,
            contribution=contr["contribution"].to_numpy(),
            cumulative_contribution=contr["cumulative_contribution"].to_numpy(),
            wcorr=wcorr,
        )

    @staticmethod
    def _x_to_ts(X_i: np.ndarray) -> np.ndarray:
        X_rev = X_i[::-1]
        return np.array(
            [X_rev.diagonal(i).mean() for i in range(-X_i.shape[0] + 1, X_i.shape[1])],
            dtype=float,
        )


class SSAKMeansClusterer:
    """
    KMeans clustering of SSA elementary reconstructed components.

    This reproduces the original project logic:
    - reconstruct each elementary component
    - extract exactly two features:
        1) dominant frequency
        2) amplitude (std)
    - cluster by KMeans
    - sum reconstructed components inside each cluster
    """

    def __init__(
        self,
        fs: int = 48,
        n_clusters: int = 3,
        random_state: int = 42,
        n_init: int = 10,
    ):
        self.fs = int(fs)
        self.n_clusters = int(n_clusters)
        self.random_state = random_state
        self.n_init = int(n_init)

    def cluster(
        self,
        ssa_result: SSAResult,
        trend_component: int | list[int] | None = None,
        max_components: int | None = None,
    ) -> SSAKMeansResult:
        X_elem = np.asarray(ssa_result.X_elem, dtype=float)
        d_total = len(X_elem)
        d_limited = d_total if max_components is None else min(d_total, int(max_components))

        components = np.arange(d_limited)

        if trend_component is not None:
            if np.isscalar(trend_component):
                excluded = {int(trend_component)}
            else:
                excluded = {int(x) for x in trend_component}
            components = np.array([c for c in components if c not in excluded], dtype=int)

        if len(components) == 0:
            raise ValueError("No components left for clustering after trend exclusion")

        components_ts = [SSADecomposer._x_to_ts(X_elem[i]) for i in components]
        features = np.array([self._get_features(ts) for ts in components_ts], dtype=float)

        n_clusters = min(self.n_clusters, len(features))
        if n_clusters < 1:
            raise ValueError("No valid features for clustering")

        model = KMeans(
            n_clusters=n_clusters,
            random_state=self.random_state,
            n_init=self.n_init,
        )
        clusters = model.fit_predict(features)

        df_anal = pd.DataFrame(
            {
                "component": components,
                "cluster": clusters,
                "frequency": features[:, 0],
                "amplitude": features[:, 1],
            }
        )

        cluster_stats = df_anal.groupby("cluster").agg(
            frequency_mean=("frequency", "mean"),
            frequency_std=("frequency", "std"),
            amplitude_mean=("amplitude", "mean"),
            amplitude_std=("amplitude", "std"),
            component_count=("component", "count"),
        )

        reconstructed: dict[int, np.ndarray] = {}
        for cluster_id in np.unique(clusters):
            comp_ids = df_anal.loc[df_anal["cluster"] == cluster_id, "component"].to_numpy(dtype=int)
            reconstructed[int(cluster_id)] = np.sum(
                [SSADecomposer._x_to_ts(X_elem[i]) for i in comp_ids],
                axis=0,
            )

        return SSAKMeansResult(
            df_anal=df_anal,
            cluster_stats=cluster_stats,
            reconstructed=reconstructed,
            labels=clusters,
            singular_values=np.asarray(ssa_result.Sigma, dtype=float),
            contribution=np.asarray(ssa_result.contribution, dtype=float),
            cumulative_contribution=np.asarray(ssa_result.cumulative_contribution, dtype=float),
        )

    def _get_features(self, ts: np.ndarray) -> tuple[float, float]:
        """
        Original feature extraction logic:
        - dominant frequency from PSD of Hanning-windowed signal
        - amplitude as std(ts)
        """
        n = len(ts)
        window = np.hanning(n)
        ts_windowed = (ts - np.mean(ts)) * window

        fft_vals = np.fft.fft(ts_windowed)
        psd = np.abs(fft_vals) ** 2
        freq = np.fft.fftfreq(n, d=1 / self.fs)

        mask = (freq > 0) & (freq < self.fs / 2)
        freq_pos = freq[mask]
        psd_pos = psd[mask]

        dominant_freq = float(freq_pos[np.argmax(psd_pos)]) if len(psd_pos) > 0 else 0.0
        amplitude = float(np.std(ts))

        return dominant_freq, amplitude


class SSAEngine:
    """
    Facade for service layer.

    Order of operations:
    1. SSA decomposition
    2. KMeans clustering of elementary reconstructed components
    3. Sum by clusters
    """

    def __init__(
        self,
        window_length: int = 48,
        fs: int = 48,
        n_clusters: int = 3,
        random_state: int = 42,
        n_init: int = 10,
        max_components: int | None = 30,
        trend_component: int | list[int] | None = None,
    ):
        self.window_length = int(window_length)
        self.fs = int(fs)
        self.n_clusters = int(n_clusters)
        self.random_state = random_state
        self.n_init = int(n_init)
        self.max_components = max_components
        self.trend_component = trend_component

    def compute_clustered_components(
        self,
        ts: pd.Series,
    ) -> SSAKMeansResult:
        ts = pd.Series(ts).astype(float).copy().sort_index()

        decomposer = SSADecomposer(ts, window_size=self.window_length)
        ssa_result = decomposer.fit()

        clusterer = SSAKMeansClusterer(
            fs=self.fs,
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=self.n_init,
        )

        return clusterer.cluster(
            ssa_result=ssa_result,
            trend_component=self.trend_component,
            max_components=self.max_components,
        )