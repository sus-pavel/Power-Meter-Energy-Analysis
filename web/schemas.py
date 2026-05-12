from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ModeType = Literal["online", "historical"]


class SparklinePoint(BaseModel):
    ts: int
    value: float


class TimeSeriesPoint(BaseModel):
    ts: int
    value: float


class SeriesResponse(BaseModel):
    source_id: str
    points: list[TimeSeriesPoint]


class StreamMetricSnapshot(BaseModel):
    metric: str
    label: str
    unit: str
    value: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    sparkline: list[SparklinePoint] = Field(default_factory=list)


class StreamMeterCard(BaseModel):
    device_id: str
    metrics: list[StreamMetricSnapshot] = Field(default_factory=list)
    last_ts: int | None = None
    source_status: str = "unknown"
    source_name: str = "kepware"


class StreamRealtimeResponse(BaseModel):
    cards: list[StreamMeterCard] = Field(default_factory=list)
    reference_ts: int | None = None


class StreamChartSeries(BaseModel):
    source_id: str
    metric: str
    label: str
    unit: str
    color: str
    points: list[TimeSeriesPoint] = Field(default_factory=list)


class StreamSeriesResponse(BaseModel):
    mode: ModeType
    year: int | None = None
    month: int | None = None
    day: int | None = None
    aggregation_min: int | None = None
    series: list[StreamChartSeries] = Field(default_factory=list)
    reference_ts: int | None = None


class SSASummaryResponse(BaseModel):
    analysis_object: str
    start_at: str
    end_at: str
    aggregation_min: int
    window_points: int
    window_hours: float
    component_count: int
    cluster_count: int
    sample_count: int
    fs: int


class SSALineSeries(BaseModel):
    label: str
    color: str
    points: list[TimeSeriesPoint] = Field(default_factory=list)


class SSACumulativePoint(BaseModel):
    component: int
    cumulative: float


class SSAScatterPoint(BaseModel):
    component: int
    cluster: int
    frequency: float
    amplitude: float
    color: str


class SSAAnalysisResponse(BaseModel):
    summary: SSASummaryResponse
    original_series: list[TimeSeriesPoint] = Field(default_factory=list)
    wcorr: list[list[float]] = Field(default_factory=list)
    cumulative_contribution: list[SSACumulativePoint] = Field(default_factory=list)
    amplitude_frequency: list[SSAScatterPoint] = Field(default_factory=list)
    grouped_series: list[SSALineSeries] = Field(default_factory=list)
    component_series: list[SSALineSeries] = Field(default_factory=list)
    cluster_series: list[SSALineSeries] = Field(default_factory=list)


class OverviewSummaryResponse(BaseModel):
    current_drpi: float | None = None
    current_total_power_kw: float | None = None
    active_meters: int
    total_meters: int
    drpi_sparkline: list[SparklinePoint] = Field(default_factory=list)
    total_power_sparkline: list[SparklinePoint] = Field(default_factory=list)
    reference_ts: int | None = None


class OverviewPowerMetersResponse(BaseModel):
    mode: ModeType
    year: int | None = None
    month: int | None = None
    series: list[SeriesResponse] = Field(default_factory=list)


class HeatmapCell(BaseModel):
    weekday: int
    weekday_label: str
    hour: int
    value: float | None


class OverviewHeatmapResponse(BaseModel):
    source_id: str
    mode: ModeType
    year: int | None = None
    month: int | None = None
    cells: list[HeatmapCell] = Field(default_factory=list)


class DRPISummaryResponse(BaseModel):
    source_id: str
    current_drpi: float | None = None
    preferred_days: list[str] = Field(default_factory=list)
    min_24h: float | None = None
    max_24h: float | None = None
    current_f1: float | None = None
    current_f2: float | None = None
    current_f3: float | None = None
    sparkline_f1: list[SparklinePoint] = Field(default_factory=list)
    sparkline_f2: list[SparklinePoint] = Field(default_factory=list)
    sparkline_f3: list[SparklinePoint] = Field(default_factory=list)
    reference_ts: int | None = None


class DRPIHistoryResponse(BaseModel):
    source_id: str
    mode: ModeType
    year: int | None = None
    month: int | None = None
    drpi: list[TimeSeriesPoint] = Field(default_factory=list)


class DRPIComponentsResponse(BaseModel):
    source_id: str
    mode: ModeType
    year: int | None = None
    month: int | None = None
    f1: list[TimeSeriesPoint] = Field(default_factory=list)
    f2: list[TimeSeriesPoint] = Field(default_factory=list)
    f3: list[TimeSeriesPoint] = Field(default_factory=list)


class SelectOption(BaseModel):
    value: str
    label: str


class CommonPageContext(BaseModel):
    title: str
    page_name: str
    meter_options: list[SelectOption] = Field(default_factory=list)
    year_options: list[int] = Field(default_factory=list)
    month_options: list[int] = Field(default_factory=list)
    defaults: dict[str, Any] = Field(default_factory=dict)
