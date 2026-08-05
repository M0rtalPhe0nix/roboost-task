from __future__ import annotations

import asyncio
import time

from adk_connectors.models.session import SessionModel
from google.adk.events.event import Event
from google.genai import types

from app.session_memory import (
    BoundedInMemorySessionService,
    BoundedMemorySessionStorage,
    recent_session_events,
)


def chat_event(index: int, timestamp: float | None = None) -> Event:
    return Event(
        author="user" if index % 2 == 0 else "pharmacy_operations_assistant",
        content=types.Content(
            role="user" if index % 2 == 0 else "model",
            parts=[types.Part(text=f"message-{index}")],
        ),
        invocation_id=f"invocation-{index}",
        timestamp=timestamp if timestamp is not None else float(index + 1),
    )


def test_recent_session_events_keeps_latest_visible_messages() -> None:
    events = [chat_event(index) for index in range(14)]

    result = recent_session_events(events, max_messages=10)

    assert [event.content.parts[0].text for event in result] == [
        f"message-{index}" for index in range(4, 14)
    ]


def test_adk_storage_physically_trims_old_events() -> None:
    async def exercise() -> tuple[int, list[str]]:
        service = BoundedInMemorySessionService(
            max_messages=10,
            max_sessions=5,
            idle_ttl_seconds=3600,
        )
        session = await service.create_session(
            app_name="app",
            user_id="user-1",
            session_id="session-1",
        )
        for index in range(14):
            await service.append_event(session, chat_event(index))
        stored = service.sessions["app"]["user-1"]["session-1"]
        return len(stored.events), [event.content.parts[0].text for event in stored.events]

    count, messages = asyncio.run(exercise())

    assert count == 10
    assert messages == [f"message-{index}" for index in range(4, 14)]


def test_adk_storage_evicts_least_recently_used_sessions() -> None:
    async def exercise() -> set[str]:
        service = BoundedInMemorySessionService(
            max_messages=10,
            max_sessions=1,
            idle_ttl_seconds=3600,
        )
        await service.create_session(app_name="app", user_id="old", session_id="old")
        service.sessions["app"]["old"]["old"].last_update_time = time.time() - 1
        await service.create_session(app_name="app", user_id="new", session_id="new")
        return set(service.sessions["app"])

    assert asyncio.run(exercise()) == {"new"}


def test_connector_metadata_storage_evicts_least_recently_used_sessions() -> None:
    async def exercise() -> set[str]:
        storage = BoundedMemorySessionStorage(max_sessions=1, idle_ttl_seconds=10**12)
        await storage.set(
            "telegram:old",
            SessionModel(
                platform_key="telegram:old",
                adk_session_id="old",
                adk_user_id="old",
                created_at=1,
                last_active=1,
            ),
        )
        await storage.set(
            "telegram:new",
            SessionModel(
                platform_key="telegram:new",
                adk_session_id="new",
                adk_user_id="new",
                created_at=2,
                last_active=2,
            ),
        )
        return set(storage._storage)

    assert asyncio.run(exercise()) == {"telegram:new"}
