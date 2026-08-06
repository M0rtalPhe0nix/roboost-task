import pytest

from message_triage.models import Intent
from message_triage.provider import _parse_decisions


def test_parse_structured_provider_decisions():
    decisions = _parse_decisions(
        {
            "id": ["c0:s1:t0"],
            "i": ["complaint"],
            "u": [True],
        }
    )
    assert decisions[0].message_id == "c0:s1:t0"
    assert decisions[0].intent is Intent.COMPLAINT
    assert decisions[0].is_urgent is True


@pytest.mark.parametrize(
    "item",
    [
        {"id": ["x"], "i": ["unknown"], "u": [False]},
        {"id": ["x"], "i": ["complaint"], "u": ["false"]},
        {"id": ["x"], "i": ["complaint", "spam"], "u": [False]},
    ],
)
def test_rejects_invalid_provider_decisions(item):
    with pytest.raises((TypeError, ValueError)):
        _parse_decisions(item)
