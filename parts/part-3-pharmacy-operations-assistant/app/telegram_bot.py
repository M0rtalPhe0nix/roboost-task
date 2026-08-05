"""Telegram transport for the pharmacy operations ADK agent."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from adk_connectors import ConnectorConfig, FormatterConfig, SessionConfig
from adk_connectors.models.incoming import IncomingMessage
from adk_connectors.models.outgoing import OutgoingMessage
from adk_connectors.telegram import TelegramConnector

from .agent import root_agent
from .config import Settings, get_settings
from .session_memory import BoundedInMemorySessionService, BoundedMemorySessionStorage

LOGGER = logging.getLogger(__name__)
PRIVATE_CHAT_TYPE = "private"


def parse_allowed_user_ids(raw_value: str) -> frozenset[str]:
    """Parse an optional comma-separated Telegram user-ID allowlist."""

    values = [value.strip() for value in raw_value.split(",") if value.strip()]
    if any(not value.isdecimal() for value in values):
        raise ValueError("TELEGRAM_ALLOWED_USER_IDS must contain only comma-separated numbers.")
    return frozenset(values)


class TelegramAuthorizationGate:
    """Allow private chats in public mode or only from configured users."""

    def __init__(
        self,
        allowed_user_ids: frozenset[str],
        public_access: bool,
        adapter: Any,
        downstream: Callable[[IncomingMessage], Awaitable[None]],
        max_concurrent_messages: int = 1,
    ) -> None:
        self.allowed_user_ids = allowed_user_ids
        self.public_access = public_access
        self.adapter = adapter
        self.downstream = downstream
        self._message_slots = asyncio.Semaphore(max_concurrent_messages)

    async def __call__(self, message: IncomingMessage) -> None:
        chat = message.raw_update.get("message", {}).get("chat", {})
        if chat.get("type") != PRIVATE_CHAT_TYPE:
            await self._deny(message, "This assistant is available only in a private chat.")
            return
        if not self.public_access and message.user_id not in self.allowed_user_ids:
            LOGGER.warning("Denied a Telegram message from a user outside the allowlist.")
            await self._deny(message, "This is a private operations assistant. Access denied.")
            return
        async with self._message_slots:
            await self.downstream(message)

    async def _deny(self, message: IncomingMessage, response: str) -> None:
        await self.adapter.send_message(
            message.chat_id,
            OutgoingMessage(chat_id=message.chat_id, text=response),
        )


def build_telegram_connector(settings: Settings | None = None) -> TelegramConnector:
    """Create the official ADK Telegram connector with an explicit access mode."""

    runtime_settings = settings or get_settings()
    if runtime_settings.telegram_bot_token is None:
        raise ValueError("TELEGRAM_BOT_TOKEN is required.")

    allowed_user_ids = parse_allowed_user_ids(runtime_settings.telegram_allowed_user_ids)
    if not runtime_settings.telegram_public_access and not allowed_user_ids:
        raise ValueError(
            "Set TELEGRAM_PUBLIC_ACCESS=true or configure TELEGRAM_ALLOWED_USER_IDS."
        )
    connector_config = ConnectorConfig(
        session=SessionConfig(ttl_seconds=runtime_settings.session_idle_ttl_seconds),
        formatter=FormatterConfig(streaming=False),
    )
    metadata_storage = BoundedMemorySessionStorage(
        max_sessions=runtime_settings.max_active_sessions,
        idle_ttl_seconds=runtime_settings.session_idle_ttl_seconds,
    )
    adk_session_service = BoundedInMemorySessionService(
        max_messages=runtime_settings.chat_history_messages,
        max_sessions=runtime_settings.max_active_sessions,
        idle_ttl_seconds=runtime_settings.session_idle_ttl_seconds,
    )
    connector = TelegramConnector(
        token=runtime_settings.telegram_bot_token.get_secret_value(),
        agent=root_agent,
        streaming=False,
        connector_config=connector_config,
        session_storage=metadata_storage,
        adk_session_service=adk_session_service,
        app_name="app",
    )
    if connector.manager is None:
        raise RuntimeError("Telegram connector did not initialize its ADK manager.")

    gate = TelegramAuthorizationGate(
        allowed_user_ids=allowed_user_ids,
        public_access=runtime_settings.telegram_public_access,
        adapter=connector.adapter,
        downstream=connector.manager.handle_incoming_message,
        max_concurrent_messages=runtime_settings.max_concurrent_messages,
    )
    connector.adapter.register_message_handler(gate)
    connector.authorization_gate = gate
    return connector


def main() -> None:
    """Validate runtime inputs and start Telegram long polling."""

    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    if not settings.operations_data_path.is_file():
        raise FileNotFoundError(f"Operations data is absent at {settings.operations_data_path}.")
    connector = build_telegram_connector(settings)
    access_mode = "public private-chat" if settings.telegram_public_access else "allowlisted"
    LOGGER.info("Starting the %s Pharmacy Operations Telegram bot.", access_mode)
    connector.start()


if __name__ == "__main__":
    main()
