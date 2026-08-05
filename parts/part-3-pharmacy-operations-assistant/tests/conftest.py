from __future__ import annotations

from collections.abc import Iterator

import pandas as pd
import pytest

from app.analytics import AnalysisPolicy, OperationsRepository


def _order(
    order_number: int,
    branch: str,
    created: pd.Timestamp,
    delivery_minutes: int,
    comment: str | None = None,
    rating: float = 5,
    invalid_pickup: bool = False,
) -> dict[str, object]:
    added = created + pd.Timedelta(minutes=10)
    pickup = added - pd.Timedelta(minutes=2) if invalid_pickup else added + pd.Timedelta(minutes=5)
    return {
        "OrderID": f"order-{order_number}",
        "CustomerID": f"customer-{order_number}",
        "CustomerComment": comment,
        "CustomerRatingAverage": rating,
        "BranchID": branch,
        "DeliveryZoneName": "Area-1" if branch == "BR-A" else "Area-2",
        "RiderID": "rider-1" if branch == "BR-A" else "rider-2",
        "Amount": 100,
        "CreatedDate": created,
        "ShiftDate": created.normalize(),
        "DeliveryTime": created + pd.Timedelta(minutes=delivery_minutes),
        "AddedToTripTime": added,
        "PickingUpTime": pickup,
    }


@pytest.fixture
def source_frame() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    number = 0
    for month, branch, delivery_minutes, count in [
        ("2026-05", "BR-A", 35, 8),
        ("2026-06", "BR-A", 70, 8),
        ("2026-05", "BR-B", 65, 8),
        ("2026-06", "BR-B", 40, 8),
        ("2026-05", "BR-C", 45, 2),
        ("2026-06", "BR-C", 90, 2),
    ]:
        for index in range(count):
            number += 1
            day = index % 4 + 1
            is_late_comment = branch == "BR-A" and month == "2026-06" and index < 2
            comment = "Order was late" if is_late_comment else None
            rows.append(
                _order(
                    number,
                    branch,
                    pd.Timestamp(f"{month}-{day:02d} 10:00:00"),
                    delivery_minutes,
                    comment=comment,
                    rating=1 if comment else 5,
                    invalid_pickup=index == 0 and branch == "BR-A" and month == "2026-06",
                )
            )
    # Make July the partial current month so June is the latest complete month.
    number += 1
    rows.append(_order(number, "BR-A", pd.Timestamp("2026-07-03 10:00:00"), 50))
    return pd.DataFrame(rows)


@pytest.fixture
def repository(source_frame: pd.DataFrame) -> Iterator[OperationsRepository]:
    policy = AnalysisPolicy(
        min_comparison_orders=3,
        min_comparison_days=2,
        min_completeness=0.75,
        long_delivery_minutes=50,
        max_results=8,
    )
    yield OperationsRepository(source_frame, policy)
