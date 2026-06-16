export interface ChartPoint {
  ts: string;
  value: number;
}

export interface TrendSeries {
  device_id: number | null;
  metric: string;
  unit: string | null;
  aggregation: string;
  points: ChartPoint[];
}

export interface TrendSummary {
  metric: string;
  aggregation: string;
  from: string | null;
  to: string | null;
  mean: number | null;
  min: number | null;
  max: number | null;
  sample_count: number;
}

export interface TrendMetrics {
  devices: { id: number; name: string; enabled: boolean }[];
  metrics: string[];
}

export interface DrpiSource {
  source_id: string;
  F1: number;
  F2: number;
  F3: number;
  R_raw: number;
  DRPI: number;
}

export interface DrpiSummary {
  latest_ts: string | null;
  sources: DrpiSource[];
}

export interface DrpiHistory {
  source_id: string;
  points: ChartPoint[];
}

export interface DrpiComponents {
  source_id: string;
  points: Array<{ ts: string; F1: number; F2: number; F3: number; DRPI: number }>;
}

export interface SSAAnalyzeRequest {
  device_ids: number[];
  metric: string;
  aggregation: string;
  from?: string | null;
  to?: string | null;
  window_points: number;
  component_count: number;
  cluster_count: number;
}

export interface SSAResult {
  original_series: ChartPoint[];
  trend_series: ChartPoint[];
  component_series: Array<{ component: number; points: ChartPoint[] }>;
  cluster_series: Array<{ cluster: number; points: ChartPoint[] }>;
  wcorr_matrix: number[][];
  cumulative_contribution: Array<{ component: number; value: number }>;
  amplitude_frequency_points: Array<{ component: number; cluster: number; frequency: number; amplitude: number }>;
  summary: Record<string, string | number>;
}
