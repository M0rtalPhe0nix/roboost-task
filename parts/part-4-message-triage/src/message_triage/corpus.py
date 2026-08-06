from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .models import ConversationTurn, CustomerMessage


class CorpusError(ValueError):
    """The source corpus does not match the expected contract."""


def load_corpus(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, list):
        raise CorpusError("corpus root must be a JSON array")
    return data


def iter_customer_messages(conversations: list[dict[str, Any]]) -> Iterator[CustomerMessage]:
    """Yield customer turns with preceding, and never future, conversation history."""
    for conversation_index, conversation in enumerate(conversations):
        try:
            seed_id = conversation["seed_id"]
            platform = conversation["platform"]
            raw_turns = conversation["messages"]
        except KeyError as exc:
            raise CorpusError(
                f"conversation {conversation_index} is missing {exc.args[0]!r}"
            ) from exc
        if not isinstance(seed_id, int) or not isinstance(platform, str):
            raise CorpusError(f"conversation {conversation_index} has invalid metadata")
        if not isinstance(raw_turns, list):
            raise CorpusError(f"conversation {conversation_index} messages must be an array")

        history: list[ConversationTurn] = []
        for turn_index, raw in enumerate(raw_turns):
            try:
                author = raw["from"]
                text = raw["text"]
                gap_minutes = raw["gap_minutes"]
            except (KeyError, TypeError) as exc:
                raise CorpusError(
                    f"conversation {conversation_index}, turn {turn_index} is malformed"
                ) from exc
            if author not in {"customer", "brand"}:
                raise CorpusError(
                    f"conversation {conversation_index}, turn {turn_index} has invalid author"
                )
            if not isinstance(text, str) or not isinstance(gap_minutes, int):
                raise CorpusError(
                    f"conversation {conversation_index}, turn {turn_index} has invalid fields"
                )

            if author == "customer":
                yield CustomerMessage(
                    conversation_index=conversation_index,
                    seed_id=seed_id,
                    turn_index=turn_index,
                    platform=platform,
                    text=text,
                    gap_minutes=gap_minutes,
                    history=tuple(history),
                )
            history.append(
                ConversationTurn(
                    turn_index=turn_index,
                    author=author,
                    text=text,
                    gap_minutes=gap_minutes,
                )
            )


def corpus_counts(conversations: list[dict[str, Any]]) -> dict[str, int]:
    all_turns = sum(len(row.get("messages", [])) for row in conversations)
    customer_turns = sum(
        turn.get("from") == "customer"
        for row in conversations
        for turn in row.get("messages", [])
    )
    return {
        "conversations": len(conversations),
        "all_turns": all_turns,
        "customer_turns": customer_turns,
        "brand_turns": all_turns - customer_turns,
    }
