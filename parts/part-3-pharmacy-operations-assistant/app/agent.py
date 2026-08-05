"""Google ADK agent and its single, allow-listed analytics tool."""

from __future__ import annotations

from typing import Any

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from .analytics import (
    AnalysisName,
    AnalysisPolicy,
    DimensionName,
    MetricName,
    OperationsDataError,
    PeriodName,
    load_repository,
)
from .config import get_settings
from .history import limit_model_history
from .prompts import SYSTEM_INSTRUCTION


def analyze_operations(
    analysis: AnalysisName,
    metric: MetricName = "delivery_duration_minutes",
    period: PeriodName = "latest_complete_month",
    dimension: DimensionName = "branch",
    limit: int = 8,
) -> dict[str, Any]:
    """Run a safe, aggregate pharmacy-operations analysis.

    Use `analysis` with exactly one of: `data_scope`, `operations_summary`,
    `branch_delivery_change`, `late_order_hotspots`, or `operational_watchouts`.
    Metrics are `delivery_duration_minutes`, `dispatch_lag_minutes`, or
    `pickup_lag_minutes`. Periods are `latest_complete_month`,
    `previous_complete_month`, or `all_time`. Hotspot dimensions are `branch`,
    `zone`, `hour`, or `rider`. The tool never accepts SQL and never returns source rows.
    """

    settings = get_settings()
    policy = AnalysisPolicy(
        min_comparison_orders=settings.min_comparison_orders,
        min_comparison_days=settings.min_comparison_days,
        min_completeness=settings.min_completeness,
        long_delivery_minutes=settings.long_delivery_minutes,
    )
    try:
        repository = load_repository(str(settings.operations_data_path), policy)
        return repository.analyze(
            analysis=analysis,
            metric=metric,
            period=period,
            dimension=dimension,
            limit=max(1, min(limit, 20)),
        )
    except OperationsDataError as error:
        return {
            "error": str(error),
            "safe_response": "The requested analysis cannot be supported from the loaded data.",
        }


settings = get_settings()

root_agent = Agent(
    name="pharmacy_operations_assistant",
    model=Gemini(
        model=settings.google_model,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description="Evidence-bound operational analytics for a 132-branch pharmacy group.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[analyze_operations],
    before_model_callback=limit_model_history(settings.chat_history_messages),
)

app = App(root_agent=root_agent, name="app")
