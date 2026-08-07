from __future__ import annotations

import json
from pathlib import Path

from google.adk.evaluation.eval_set import EvalSet
from google.adk.evaluation.local_eval_sets_manager import LocalEvalSetsManager

PROJECT_DIR = Path(__file__).parents[1]
EVAL_SET_PATH = PROJECT_DIR / "app" / "pharmacy_operations_core_behaviors_v1.evalset.json"


def test_eval_set_matches_the_installed_adk_schema() -> None:
    eval_set = EvalSet.model_validate_json(EVAL_SET_PATH.read_text(encoding="utf-8"))

    assert eval_set.eval_set_id == "pharmacy_operations_core_behaviors_v1"
    assert len(eval_set.eval_cases) == 12
    assert len({case.eval_id for case in eval_set.eval_cases}) == len(eval_set.eval_cases)
    assert all(
        case.session_input and case.session_input.app_name == "app"
        for case in eval_set.eval_cases
    )


def test_eval_set_is_discoverable_by_adk_web() -> None:
    manager = LocalEvalSetsManager(agents_dir=str(PROJECT_DIR))

    assert "pharmacy_operations_core_behaviors_v1" in manager.list_eval_sets("app")


def test_eval_set_covers_supported_routing_and_safety_boundaries() -> None:
    payload = json.loads(EVAL_SET_PATH.read_text(encoding="utf-8"))
    cases = {case["eval_id"]: case for case in payload["eval_cases"]}

    supported_analyses = {
        tool_use["args"]["analysis"]
        for case in payload["eval_cases"]
        for invocation in case["conversation"]
        for tool_use in invocation["intermediate_data"]["tool_uses"]
    }
    assert supported_analyses == {
        "data_scope",
        "operations_summary",
        "branch_delivery_change",
        "late_order_hotspots",
        "operational_watchouts",
    }

    refusal_ids = {
        "unsupported_stockout_causality",
        "unsupported_staffing_inference",
        "unsupported_patient_harm_inference",
        "raw_row_and_identifier_refusal",
    }
    for eval_id in refusal_ids:
        assert cases[eval_id]["conversation"][0]["intermediate_data"]["tool_uses"] == []

    multi_turn = cases["multi_turn_branch_to_rider_drilldown"]["conversation"]
    dimensions = [
        turn["intermediate_data"]["tool_uses"][0]["args"]["dimension"]
        for turn in multi_turn
    ]
    assert dimensions == [
        "branch",
        "rider",
    ]
