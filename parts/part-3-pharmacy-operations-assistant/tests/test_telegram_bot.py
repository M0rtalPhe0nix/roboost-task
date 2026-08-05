from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest
from adk_connectors.models.incoming import IncomingMessage
from pydantic import SecretStr

from app.config import Settings
from app.telegram_bot import (
    TelegramAuthorizationGate,
    build_telegram_connector,
    parse_allowed_user_ids,
)


def incoming_message(user_id: str = "123", chat_type: str = "private") -> IncomingMessage:
    return IncomingMessage(
        platform="telegram",
        user_id=user_id,
        chat_id="chat-1",
        message_id="message-1",
        text="What needs attention?",
        raw_update={"message": {"chat": {"type": chat_type}}},
    )


def test_allowed_user_ids_are_normalized_and_deduplicated() -> None:
    assert parse_allowed_user_ids(" 123,456,123 ") == frozenset({"123", "456"})


def test_allowed_user_ids_may_be_empty_in_public_mode() -> None:
    assert parse_allowed_user_ids("") == frozenset()


def test_allowed_user_ids_must_be_numbers() -> None:
    with pytest.raises(ValueError, match="TELEGRAM_ALLOWED_USER_IDS"):
        parse_allowed_user_ids("123,person")


def test_authorized_private_message_reaches_agent() -> None:
    adapter = AsyncMock()
    downstream = AsyncMock()
    gate = TelegramAuthorizationGate(frozenset({"123"}), False, adapter, downstream)
    message = incoming_message()

    asyncio.run(gate(message))

    downstream.assert_awaited_once_with(message)
    adapter.send_message.assert_not_awaited()


@pytest.mark.parametrize(
    ("message", "expected_text"),
    [
        (incoming_message(user_id="999"), "Access denied"),
        (incoming_message(chat_type="group"), "only in a private chat"),
    ],
)
def test_unauthorized_or_group_message_is_denied(
    message: IncomingMessage, expected_text: str
) -> None:
    adapter = AsyncMock()
    downstream = AsyncMock()
    gate = TelegramAuthorizationGate(frozenset({"123"}), False, adapter, downstream)

    asyncio.run(gate(message))

    downstream.assert_not_awaited()
    outgoing = adapter.send_message.await_args.args[1]
    assert expected_text in outgoing.text
    assert outgoing.chat_id == message.chat_id


def test_public_mode_allows_any_user_in_a_private_chat() -> None:
    adapter = AsyncMock()
    downstream = AsyncMock()
    gate = TelegramAuthorizationGate(frozenset(), True, adapter, downstream)
    message = incoming_message(user_id="999")

    asyncio.run(gate(message))

    downstream.assert_awaited_once_with(message)
    adapter.send_message.assert_not_awaited()


def test_public_mode_still_rejects_group_chats() -> None:
    adapter = AsyncMock()
    downstream = AsyncMock()
    gate = TelegramAuthorizationGate(frozenset(), True, adapter, downstream)
    message = incoming_message(user_id="999", chat_type="group")

    asyncio.run(gate(message))

    downstream.assert_not_awaited()
    assert "only in a private chat" in adapter.send_message.await_args.args[1].text


def test_build_connector_registers_access_gate(monkeypatch) -> None:
    class FakeAdapter:
        def __init__(self) -> None:
            self.handler = None

        def register_message_handler(self, handler) -> None:
            self.handler = handler

    class FakeManager:
        async def handle_incoming_message(self, _message: IncomingMessage) -> None:
            return None

    class FakeConnector:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            self.adapter = FakeAdapter()
            self.manager = FakeManager()

    monkeypatch.setattr("app.telegram_bot.TelegramConnector", FakeConnector)
    settings = Settings(
        _env_file=None,
        telegram_bot_token=SecretStr("bot-token"),
        telegram_allowed_user_ids="123",
    )

    connector = build_telegram_connector(settings)

    assert connector.kwargs["token"] == "bot-token"
    assert connector.kwargs["streaming"] is False
    assert connector.kwargs["app_name"] == "app"
    assert isinstance(connector.adapter.handler, TelegramAuthorizationGate)


def test_build_connector_requires_bot_token() -> None:
    settings = Settings(_env_file=None, telegram_allowed_user_ids="123")

    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        build_telegram_connector(settings)


def test_build_connector_requires_an_explicit_access_mode() -> None:
    settings = Settings(_env_file=None, telegram_bot_token=SecretStr("bot-token"))

    with pytest.raises(ValueError, match="TELEGRAM_PUBLIC_ACCESS"):
        build_telegram_connector(settings)


def test_build_connector_accepts_public_mode(monkeypatch) -> None:
    class FakeAdapter:
        def register_message_handler(self, handler) -> None:
            self.handler = handler

    class FakeManager:
        async def handle_incoming_message(self, _message: IncomingMessage) -> None:
            return None

    class FakeConnector:
        def __init__(self, **_kwargs) -> None:
            self.adapter = FakeAdapter()
            self.manager = FakeManager()

    monkeypatch.setattr("app.telegram_bot.TelegramConnector", FakeConnector)
    settings = Settings(
        _env_file=None,
        telegram_bot_token=SecretStr("bot-token"),
        telegram_public_access=True,
    )

    connector = build_telegram_connector(settings)

    assert connector.authorization_gate.public_access is True
    assert connector.authorization_gate.allowed_user_ids == frozenset()
