from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.agent import analyze_operations, root_agent
from app.prompts import SYSTEM_INSTRUCTION


def test_agent_exposes_only_the_aggregate_analysis_tool() -> None:
    assert root_agent.name == "pharmacy_operations_assistant"
    assert len(root_agent.tools) == 1
    assert root_agent.before_model_callback is not None


def test_prompt_requires_tools_and_declines_unsupported_topics() -> None:
    normalized = " ".join(SYSTEM_INSTRUCTION.split())
    assert "Use the `analyze_operations` tool for every factual claim" in normalized
    assert "medication or patient safety" in SYSTEM_INSTRUCTION
    assert "definitive root causes" in SYSTEM_INSTRUCTION
    assert "do not expose" in SYSTEM_INSTRUCTION.lower()


def test_tool_returns_a_safe_error_when_data_is_unavailable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    unavailable_settings = SimpleNamespace(
        operations_data_path=tmp_path / "missing.xlsx",
        min_comparison_orders=50,
        min_comparison_days=14,
        min_completeness=0.90,
        long_delivery_minutes=90,
    )
    monkeypatch.setattr("app.agent.get_settings", lambda: unavailable_settings)
    result = analyze_operations("data_scope")

    assert "error" in result
    assert "safe_response" in result


def test_worker_image_uses_prepared_runtime_data() -> None:
    dockerfile = Path(__file__).parents[1] / "Dockerfile"
    content = dockerfile.read_text(encoding="utf-8")

    assert "scripts/prepare_runtime_data.py" in content
    assert "OPERATIONS_DATA_PATH=/app/data/operations.runtime.csv.gz" in content
