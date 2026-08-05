"""Deterministic, read-only analytics used by the conversational agent."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import pandas as pd

MetricName = Literal[
    "delivery_duration_minutes",
    "dispatch_lag_minutes",
    "pickup_lag_minutes",
]
PeriodName = Literal["latest_complete_month", "previous_complete_month", "all_time"]
DimensionName = Literal["branch", "zone", "hour", "rider"]
AnalysisName = Literal[
    "data_scope",
    "branch_delivery_change",
    "late_order_hotspots",
    "operational_watchouts",
    "operations_summary",
]

METRIC_DEFINITIONS: dict[str, str] = {
    "delivery_duration_minutes": "DeliveryTime - CreatedDate (minutes)",
    "dispatch_lag_minutes": "AddedToTripTime - CreatedDate (minutes)",
    "pickup_lag_minutes": "PickingUpTime - AddedToTripTime (minutes)",
}

COLUMN_NAMES = {
    "OrderID",
    "CustomerID",
    "CustomerComment",
    "CustomerRatingAverage",
    "BranchID",
    "DeliveryZoneName",
    "RiderID",
    "Amount",
    "CreatedDate",
    "ShiftDate",
    "DeliveryTime",
    "AddedToTripTime",
    "PickingUpTime",
}

DATE_COLUMNS = [
    "CreatedDate",
    "ShiftDate",
    "DeliveryTime",
    "AddedToTripTime",
    "PickingUpTime",
]

LATE_COMMENT_TERMS = (
    "late",
    "delay",
    "delayed",
    "hours",
    "hour",
    "متأخر",
    "تأخير",
    "تاخير",
    "ساع",
    "وصل بعد",
)


class OperationsDataError(ValueError):
    """Raised when the source data cannot support safe analysis."""


@dataclass(frozen=True)
class AnalysisPolicy:
    """Versioned reliability and display thresholds."""

    min_comparison_orders: int = 50
    min_comparison_days: int = 14
    min_completeness: float = 0.90
    long_delivery_minutes: float = 90.0
    max_results: int = 8


@dataclass(frozen=True)
class DateWindow:
    """Inclusive start and exclusive end dates for a named period."""

    name: str
    start: pd.Timestamp
    end: pd.Timestamp

    @property
    def label(self) -> str:
        last_day = (self.end - pd.Timedelta(days=1)).date().isoformat()
        return f"{self.start.date().isoformat()} to {last_day}"


def _json_value(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {str(key): _json_value(value) for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


class OperationsRepository:
    """Loads the workbook once and exposes only aggregated, allow-listed analyses."""

    def __init__(self, frame: pd.DataFrame, policy: AnalysisPolicy | None = None) -> None:
        self.policy = policy or AnalysisPolicy()
        self.frame = self._prepare(frame)
        self.data_start = self.frame["CreatedDate"].min()
        self.data_end = self.frame["CreatedDate"].max()

    @classmethod
    def from_path(
        cls, path: str | Path, policy: AnalysisPolicy | None = None
    ) -> OperationsRepository:
        source = Path(path)
        if not source.exists():
            raise OperationsDataError(
                f"Operations data was not found at {source}. Set OPERATIONS_DATA_PATH."
            )
        if source.suffix.lower() == ".csv":
            frame = pd.read_csv(source)
        elif source.suffix.lower() in {".xlsx", ".xlsm"}:
            frame = pd.read_excel(source, sheet_name="Data", engine="openpyxl")
        else:
            raise OperationsDataError("Only .xlsx, .xlsm, and .csv sources are supported.")
        return cls(frame, policy)

    @staticmethod
    def _prepare(raw: pd.DataFrame) -> pd.DataFrame:
        missing_columns = sorted(COLUMN_NAMES - set(raw.columns))
        if missing_columns:
            raise OperationsDataError(f"Missing required columns: {', '.join(missing_columns)}")

        frame = raw.copy()
        for column in DATE_COLUMNS:
            frame[column] = pd.to_datetime(frame[column], errors="coerce")
        if frame["CreatedDate"].isna().any():
            raise OperationsDataError("CreatedDate contains missing or invalid values.")
        if frame["OrderID"].duplicated().any():
            raise OperationsDataError("OrderID must be unique.")

        frame["delivery_duration_minutes"] = (
            frame["DeliveryTime"] - frame["CreatedDate"]
        ).dt.total_seconds().div(60)
        frame["dispatch_lag_minutes"] = (
            frame["AddedToTripTime"] - frame["CreatedDate"]
        ).dt.total_seconds().div(60)
        frame["pickup_lag_minutes"] = (
            frame["PickingUpTime"] - frame["AddedToTripTime"]
        ).dt.total_seconds().div(60)

        for metric in METRIC_DEFINITIONS:
            frame.loc[frame[metric] < 0, metric] = pd.NA

        comments = frame["CustomerComment"].fillna("").astype(str).str.casefold()
        pattern = "|".join(re.escape(term) for term in LATE_COMMENT_TERMS)
        frame["late_comment_signal"] = comments.str.contains(pattern, regex=True)
        frame["long_delivery"] = (
            frame["delivery_duration_minutes"] > 90.0
        )  # overwritten per policy in grouped analysis
        frame["delivery_hour"] = frame["CreatedDate"].dt.hour
        return frame

    def _window(self, period: PeriodName) -> DateWindow:
        current_month = self.data_end.to_period("M").start_time
        latest_complete_start = current_month - pd.offsets.MonthBegin(1)
        previous_start = latest_complete_start - pd.offsets.MonthBegin(1)
        if period == "latest_complete_month":
            return DateWindow(period, latest_complete_start, current_month)
        if period == "previous_complete_month":
            return DateWindow(period, previous_start, latest_complete_start)
        if period == "all_time":
            return DateWindow(
                period,
                self.data_start.normalize(),
                self.data_end.normalize() + pd.Timedelta(days=1),
            )
        raise OperationsDataError(f"Unsupported period: {period}")

    def _slice(self, window: DateWindow) -> pd.DataFrame:
        return self.frame.loc[
            (self.frame["CreatedDate"] >= window.start)
            & (self.frame["CreatedDate"] < window.end)
        ].copy()

    def _strength(self, observations: int, active_days: int, completeness: float) -> str:
        if observations >= 100 and active_days >= 20 and completeness >= 0.95:
            return "high"
        if (
            observations >= self.policy.min_comparison_orders
            and active_days >= self.policy.min_comparison_days
            and completeness >= self.policy.min_completeness
        ):
            return "medium"
        return "low"

    def _summary(self, data: pd.DataFrame, metric: MetricName) -> dict[str, Any]:
        valid = data[metric].dropna()
        count = int(len(data))
        valid_count = int(valid.size)
        active_days = int(data["CreatedDate"].dt.date.nunique()) if count else 0
        completeness = valid_count / count if count else 0.0
        return {
            "orders": count,
            "valid_observations": valid_count,
            "active_days": active_days,
            "completeness": round(completeness, 4),
            "median_minutes": round(float(valid.median()), 1) if valid_count else None,
            "p90_minutes": round(float(valid.quantile(0.90)), 1) if valid_count else None,
            "evidence_strength": self._strength(valid_count, active_days, completeness),
        }

    def data_scope(self) -> dict[str, Any]:
        comments = int(self.frame["CustomerComment"].notna().sum())
        return {
            "analysis": "data_scope",
            "data_window": (
                f"{self.data_start.date().isoformat()} to {self.data_end.date().isoformat()}"
            ),
            "orders": int(len(self.frame)),
            "branches": int(self.frame["BranchID"].nunique()),
            "zones": int(self.frame["DeliveryZoneName"].nunique()),
            "riders": int(self.frame["RiderID"].nunique()),
            "orders_with_comments": comments,
            "comment_coverage": round(comments / len(self.frame), 4),
            "supported_metrics": METRIC_DEFINITIONS,
            "privacy": "Only aggregate results and pseudonymous operational IDs are returned.",
        }

    def operations_summary(self, period: PeriodName) -> dict[str, Any]:
        window = self._window(period)
        data = self._slice(window)
        if data.empty:
            raise OperationsDataError(f"No orders exist in {window.label}.")
        low_rating_count = int((data["CustomerRatingAverage"] <= 2).sum())
        comment_count = int(data["CustomerComment"].notna().sum())
        return {
            "analysis": "operations_summary",
            "period": window.label,
            "metrics": {
                metric: self._summary(data, metric) for metric in METRIC_DEFINITIONS
            },
            "rating_signals": {
                "low_rating_orders": low_rating_count,
                "low_rating_rate": round(low_rating_count / len(data), 4),
            },
            "customer_reported_signals": {
                "comments": comment_count,
                "late_delivery_comment_signals": int(data["late_comment_signal"].sum()),
                "comment_coverage": round(comment_count / len(data), 4),
            },
            "definitions": METRIC_DEFINITIONS,
        }

    def compare_branches(self, metric: MetricName) -> dict[str, Any]:
        if metric not in METRIC_DEFINITIONS:
            raise OperationsDataError(f"Unsupported metric: {metric}")
        current_window = self._window("latest_complete_month")
        previous_window = self._window("previous_complete_month")
        current = self._branch_period_summary(self._slice(current_window), metric, "current")
        previous = self._branch_period_summary(self._slice(previous_window), metric, "previous")
        comparison = current.merge(previous, on="BranchID", how="inner")
        eligible = comparison.loc[
            (comparison["current_valid_observations"] >= self.policy.min_comparison_orders)
            & (comparison["previous_valid_observations"] >= self.policy.min_comparison_orders)
            & (comparison["current_active_days"] >= self.policy.min_comparison_days)
            & (comparison["previous_active_days"] >= self.policy.min_comparison_days)
            & (comparison["current_completeness"] >= self.policy.min_completeness)
            & (comparison["previous_completeness"] >= self.policy.min_completeness)
        ].copy()
        eligible["change_minutes"] = (
            eligible["current_median_minutes"] - eligible["previous_median_minutes"]
        )
        eligible["change_percent"] = (
            eligible["change_minutes"] / eligible["previous_median_minutes"] * 100
        )
        eligible["evidence_strength"] = eligible.apply(
            lambda row: min(
                self._strength(
                    int(row["current_valid_observations"]),
                    int(row["current_active_days"]),
                    float(row["current_completeness"]),
                ),
                self._strength(
                    int(row["previous_valid_observations"]),
                    int(row["previous_active_days"]),
                    float(row["previous_completeness"]),
                ),
                key={"low": 0, "medium": 1, "high": 2}.get,
            ),
            axis=1,
        )
        eligible = eligible.sort_values("change_minutes", ascending=False)
        columns = [
            "BranchID",
            "change_minutes",
            "change_percent",
            "current_median_minutes",
            "previous_median_minutes",
            "current_valid_observations",
            "previous_valid_observations",
            "current_active_days",
            "previous_active_days",
            "current_completeness",
            "previous_completeness",
            "evidence_strength",
        ]
        displayed = eligible.head(self.policy.max_results)[columns].round(3)
        return {
            "analysis": "branch_delivery_change",
            "metric": metric,
            "definition": METRIC_DEFINITIONS[metric],
            "current_period": current_window.label,
            "comparison_period": previous_window.label,
            "comparison_floor": {
                "minimum_valid_orders_per_period": self.policy.min_comparison_orders,
                "minimum_active_days_per_period": self.policy.min_comparison_days,
                "minimum_metric_completeness": self.policy.min_completeness,
            },
            "eligible_branches": int(len(eligible)),
            "suppressed_branches": int(len(comparison) - len(eligible)),
            "largest_increases": _records(displayed),
            "interpretation": (
                "Positive change means the median duration or lag increased (worsened)."
            ),
        }

    def _branch_period_summary(
        self, data: pd.DataFrame, metric: MetricName, prefix: str
    ) -> pd.DataFrame:
        grouped = data.groupby("BranchID", dropna=False)
        result = grouped.agg(
            orders=("OrderID", "size"),
            valid_observations=(metric, "count"),
            active_days=("CreatedDate", lambda values: values.dt.date.nunique()),
            median_minutes=(metric, "median"),
        ).reset_index()
        result["completeness"] = result["valid_observations"] / result["orders"]
        return result.rename(
            columns={column: f"{prefix}_{column}" for column in result if column != "BranchID"}
        )

    def hotspots(
        self, dimension: DimensionName, period: PeriodName, limit: int | None = None
    ) -> dict[str, Any]:
        dimension_columns = {
            "branch": "BranchID",
            "zone": "DeliveryZoneName",
            "hour": "delivery_hour",
            "rider": "RiderID",
        }
        if dimension not in dimension_columns:
            raise OperationsDataError(f"Unsupported dimension: {dimension}")
        window = self._window(period)
        data = self._slice(window)
        data["long_delivery"] = (
            data["delivery_duration_minutes"] > self.policy.long_delivery_minutes
        )
        column = dimension_columns[dimension]
        grouped = data.dropna(subset=[column]).groupby(column, dropna=False).agg(
            orders=("OrderID", "size"),
            valid_delivery_observations=("delivery_duration_minutes", "count"),
            active_days=("CreatedDate", lambda values: values.dt.date.nunique()),
            long_delivery_orders=("long_delivery", "sum"),
            median_delivery_minutes=("delivery_duration_minutes", "median"),
            late_comment_signals=("late_comment_signal", "sum"),
            comments=("CustomerComment", "count"),
        ).reset_index()
        grouped["completeness"] = grouped["valid_delivery_observations"] / grouped["orders"]
        floor = self.policy.min_comparison_orders if dimension in {"branch", "hour"} else 20
        grouped = grouped.loc[
            (grouped["valid_delivery_observations"] >= floor)
            & (grouped["completeness"] >= self.policy.min_completeness)
        ].copy()
        grouped["long_delivery_rate"] = (
            grouped["long_delivery_orders"] / grouped["valid_delivery_observations"]
        )
        grouped["evidence_strength"] = grouped.apply(
            lambda row: self._strength(
                int(row["valid_delivery_observations"]),
                int(row["active_days"]),
                float(row["completeness"]),
            ),
            axis=1,
        )
        grouped = grouped.sort_values(
            ["long_delivery_rate", "long_delivery_orders"], ascending=False
        )
        result_limit = min(limit or self.policy.max_results, 20)
        displayed = grouped.head(result_limit).round(4)
        return {
            "analysis": "late_order_hotspots",
            "period": window.label,
            "dimension": dimension,
            "definition": (
                f"Long delivery means {METRIC_DEFINITIONS['delivery_duration_minutes']} "
                f"> {self.policy.long_delivery_minutes:g} minutes; this is an analysis "
                "threshold, not a contractual SLA."
            ),
            "minimum_valid_orders_per_group": floor,
            "eligible_groups": int(len(grouped)),
            "hotspots": _records(displayed),
            "customer_signal_note": (
                "Late-comment signals are simple Arabic/English keyword matches and are "
                "shown separately from measured delivery timing."
            ),
        }

    def watchouts(self) -> dict[str, Any]:
        summary = self.operations_summary("latest_complete_month")
        previous = self.operations_summary("previous_complete_month")
        branches = self.compare_branches("delivery_duration_minutes")
        current_rating = summary["rating_signals"]["low_rating_rate"]
        previous_rating = previous["rating_signals"]["low_rating_rate"]
        invalid_intervals = {
            metric: int(self.frame[metric].isna().sum()) for metric in METRIC_DEFINITIONS
        }
        return {
            "analysis": "operational_watchouts",
            "current_period": summary["period"],
            "comparison_period": previous["period"],
            "measured_contributors": {
                "largest_comparable_branch_delivery_increases": branches["largest_increases"][:5],
                "eligible_branches": branches["eligible_branches"],
                "suppressed_branches": branches["suppressed_branches"],
                "overall_delivery": summary["metrics"]["delivery_duration_minutes"],
            },
            "customer_reported_signals": summary["customer_reported_signals"],
            "rating_signal": {
                "current_low_rating_rate": current_rating,
                "previous_low_rating_rate": previous_rating,
                "change_percentage_points": round((current_rating - previous_rating) * 100, 2),
            },
            "data_quality": {
                "invalid_or_missing_metric_observations_all_time": invalid_intervals,
                "warning": (
                    "Negative or missing timestamp intervals are excluded from the affected "
                    "metric and reduce its completeness and Evidence Strength."
                ),
            },
            "causality_note": (
                "These are observed changes and signals, not proven root causes. Validate with "
                "operational context before acting."
            ),
        }

    def analyze(
        self,
        analysis: AnalysisName,
        metric: MetricName = "delivery_duration_minutes",
        period: PeriodName = "latest_complete_month",
        dimension: DimensionName = "branch",
        limit: int = 8,
    ) -> dict[str, Any]:
        """Execute one allow-listed analysis without accepting SQL or source-row access."""

        if analysis == "data_scope":
            return self.data_scope()
        if analysis == "branch_delivery_change":
            return self.compare_branches(metric)
        if analysis == "late_order_hotspots":
            return self.hotspots(dimension, period, limit)
        if analysis == "operational_watchouts":
            return self.watchouts()
        if analysis == "operations_summary":
            return self.operations_summary(period)
        raise OperationsDataError(f"Unsupported analysis: {analysis}")


@lru_cache(maxsize=4)
def load_repository(path: str, policy: AnalysisPolicy) -> OperationsRepository:
    """Cache immutable repositories by source path and reliability policy."""

    return OperationsRepository.from_path(path, policy)
