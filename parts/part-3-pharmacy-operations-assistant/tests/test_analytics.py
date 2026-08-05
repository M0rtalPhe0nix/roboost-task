from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.analytics import OperationsDataError, OperationsRepository


def test_derives_metrics_and_excludes_negative_intervals(
    repository: OperationsRepository,
) -> None:
    summary = repository.operations_summary("latest_complete_month")

    assert summary["period"] == "2026-06-01 to 2026-06-30"
    assert summary["metrics"]["dispatch_lag_minutes"]["median_minutes"] == 10.0
    assert summary["metrics"]["pickup_lag_minutes"]["valid_observations"] == 17
    assert summary["metrics"]["pickup_lag_minutes"]["completeness"] == pytest.approx(
        17 / 18, abs=0.0001
    )


def test_branch_comparison_suppresses_sparse_branches(
    repository: OperationsRepository,
) -> None:
    result = repository.compare_branches("delivery_duration_minutes")

    assert result["eligible_branches"] == 2
    assert result["suppressed_branches"] == 1
    assert result["largest_increases"][0]["BranchID"] == "BR-A"
    assert result["largest_increases"][0]["change_minutes"] == 35


def test_hotspots_keep_measured_and_comment_signals_separate(
    repository: OperationsRepository,
) -> None:
    result = repository.hotspots("branch", "latest_complete_month")

    branch_a = next(item for item in result["hotspots"] if item["BranchID"] == "BR-A")
    assert branch_a["long_delivery_orders"] == 8
    assert branch_a["late_comment_signals"] == 2
    assert "not a contractual SLA" in result["definition"]
    assert "shown separately" in result["customer_signal_note"]


def test_aggregate_results_do_not_expose_customer_or_order_ids(
    repository: OperationsRepository,
) -> None:
    payload = json.dumps(repository.watchouts())

    assert "CustomerID" not in payload
    assert "OrderID" not in payload
    assert "customer-" not in payload
    assert "order-" not in payload


def test_rejects_non_allowlisted_analysis(repository: OperationsRepository) -> None:
    with pytest.raises(OperationsDataError, match="Unsupported analysis"):
        repository.analyze("run_sql")  # type: ignore[arg-type]


def test_routes_every_allowlisted_analysis(repository: OperationsRepository) -> None:
    assert repository.analyze("data_scope")["analysis"] == "data_scope"
    assert repository.analyze("operations_summary")["analysis"] == "operations_summary"
    assert repository.analyze("branch_delivery_change")["analysis"] == "branch_delivery_change"
    assert repository.analyze("late_order_hotspots")["analysis"] == "late_order_hotspots"
    assert repository.analyze("operational_watchouts")["analysis"] == "operational_watchouts"


def test_supports_all_allowlisted_hotspot_dimensions(
    repository: OperationsRepository,
) -> None:
    for dimension in ["zone", "hour", "rider"]:
        result = repository.hotspots(dimension, "all_time")  # type: ignore[arg-type]
        assert result["dimension"] == dimension


def test_rejects_unknown_metric_period_and_dimension(
    repository: OperationsRepository,
) -> None:
    with pytest.raises(OperationsDataError, match="Unsupported metric"):
        repository.compare_branches("average_speed")  # type: ignore[arg-type]
    with pytest.raises(OperationsDataError, match="Unsupported period"):
        repository.operations_summary("next_month")  # type: ignore[arg-type]
    with pytest.raises(OperationsDataError, match="Unsupported dimension"):
        repository.hotspots("customer", "all_time")  # type: ignore[arg-type]


def test_loads_csv_and_rejects_unknown_file_types(
    repository: OperationsRepository, tmp_path: Path
) -> None:
    source_columns = [
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
    ]
    csv_path = tmp_path / "operations.csv"
    repository.frame[source_columns].to_csv(csv_path, index=False)

    loaded = OperationsRepository.from_path(csv_path, repository.policy)
    assert len(loaded.frame) == len(repository.frame)

    bad_path = tmp_path / "operations.json"
    bad_path.write_text("{}")
    with pytest.raises(OperationsDataError, match="Only .xlsx"):
        OperationsRepository.from_path(bad_path)


def test_validates_source_contract(repository: OperationsRepository) -> None:
    missing_column = repository.frame.drop(columns=["BranchID"])
    with pytest.raises(OperationsDataError, match="Missing required columns"):
        OperationsRepository(missing_column)

    duplicated = repository.frame.copy()
    duplicated.loc[1, "OrderID"] = duplicated.loc[0, "OrderID"]
    with pytest.raises(OperationsDataError, match="OrderID must be unique"):
        OperationsRepository(duplicated)
