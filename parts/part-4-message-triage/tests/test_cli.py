import argparse
import json
from decimal import Decimal

import pytest

from message_triage.budget import Pricing
from message_triage.cli import _configuration_hash, _prepare_run_state, main


def write_corpus(path):
    path.write_text(
        json.dumps(
            [
                {
                    "seed_id": 1,
                    "platform": "x",
                    "messages": [
                        {"from": "customer", "text": "hello", "gap_minutes": 0}
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )


def run_args(tmp_path, input_path):
    return argparse.Namespace(
        input=input_path,
        output=tmp_path / "out.jsonl",
        ledger=tmp_path / "ledger.jsonl",
        budget_usd=Decimal("0.80"),
        batch_size=50,
        max_output_tokens=2048,
        resume=False,
        accept_config_change=False,
    )


def test_paid_run_requires_explicit_flag_before_provider_initialization(tmp_path):
    corpus = tmp_path / "corpus.json"
    write_corpus(corpus)

    with pytest.raises(SystemExit, match="explicit --allow-paid-api"):
        main(["run", "--input", str(corpus)])


def test_resume_rejects_changed_configuration(tmp_path):
    corpus = tmp_path / "corpus.json"
    write_corpus(corpus)
    args = run_args(tmp_path, corpus)
    original_hash = _configuration_hash(args, Pricing())
    state_path = tmp_path / "out.jsonl.state.json"
    _prepare_run_state(args, state_path, original_hash)

    args.resume = True
    args.batch_size = 20
    changed_hash = _configuration_hash(args, Pricing())

    with pytest.raises(SystemExit, match="configuration has changed"):
        _prepare_run_state(args, state_path, changed_hash)


def test_explicit_config_change_is_allowed_before_model_results(tmp_path):
    corpus = tmp_path / "corpus.json"
    write_corpus(corpus)
    args = run_args(tmp_path, corpus)
    original_hash = _configuration_hash(args, Pricing())
    state_path = tmp_path / "out.jsonl.state.json"
    _prepare_run_state(args, state_path, original_hash)
    args.output.write_text(
        json.dumps({"decision_source": "rule_gate"}) + "\n", encoding="utf-8"
    )

    args.resume = True
    args.accept_config_change = True
    args.batch_size = 20
    changed_hash = _configuration_hash(args, Pricing())
    _prepare_run_state(args, state_path, changed_hash)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["configuration_hash"] == changed_hash
    assert state["previous_configuration_hashes"] == [original_hash]


def test_fresh_run_refuses_to_overwrite_artifacts(tmp_path):
    corpus = tmp_path / "corpus.json"
    write_corpus(corpus)
    args = run_args(tmp_path, corpus)
    args.output.write_text("existing", encoding="utf-8")

    with pytest.raises(SystemExit, match="refusing to overwrite"):
        _prepare_run_state(args, tmp_path / "state.json", "hash")
