import json

import pytest

from message_triage.corpus import CorpusError, corpus_counts, iter_customer_messages, load_corpus


def test_yields_only_customer_turns_with_past_history(tmp_path):
    rows = [
        {
            "seed_id": 7,
            "platform": "instagram",
            "messages": [
                {"from": "customer", "text": "where is it?", "gap_minutes": 0},
                {"from": "brand", "text": "checking", "gap_minutes": 1},
                {"from": "customer", "text": "thanks", "gap_minutes": 2},
                {"from": "brand", "text": "future reply", "gap_minutes": 3},
            ],
        }
    ]
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(rows), encoding="utf-8")

    messages = list(iter_customer_messages(load_corpus(path)))

    assert [message.turn_index for message in messages] == [0, 2]
    assert messages[0].history == ()
    assert [turn.text for turn in messages[1].history] == ["where is it?", "checking"]
    assert "future reply" not in {turn.text for message in messages for turn in message.history}


def test_message_id_remains_unique_when_seed_ids_repeat():
    row = {
        "seed_id": 2,
        "platform": "x",
        "messages": [{"from": "customer", "text": "hello", "gap_minutes": 0}],
    }

    messages = list(iter_customer_messages([row, row]))

    assert messages[0].seed_id == messages[1].seed_id
    assert messages[0].message_id != messages[1].message_id


def test_counts_brand_turns_separately():
    rows = [
        {
            "messages": [
                {"from": "customer"},
                {"from": "brand"},
                {"from": "customer"},
            ]
        }
    ]
    assert corpus_counts(rows) == {
        "conversations": 1,
        "all_turns": 3,
        "customer_turns": 2,
        "brand_turns": 1,
    }


def test_rejects_unknown_authors():
    rows = [
        {
            "seed_id": 1,
            "platform": "x",
            "messages": [{"from": "agent", "text": "hi", "gap_minutes": 0}],
        }
    ]
    with pytest.raises(CorpusError, match="invalid author"):
        list(iter_customer_messages(rows))
