"""Bound process-local connector and ADK session memory."""

from __future__ import annotations

import time

from adk_connectors.models.session import SessionModel
from adk_connectors.storage.memory import MemorySessionStorage
from google.adk.events.event import Event
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.sessions.session import Session

from .history import is_visible_chat_message


def recent_session_events(events: list[Event], max_messages: int) -> list[Event]:
    """Keep the latest visible chat messages and their subsequent ADK events."""

    visible_messages = 0
    for index in range(len(events) - 1, -1, -1):
        content = events[index].content
        if content is None or not is_visible_chat_message(content):
            continue
        visible_messages += 1
        if visible_messages == max_messages:
            return events[index:]
    return events


class BoundedMemorySessionStorage(MemorySessionStorage):
    """Connector metadata storage with idle and least-recently-used eviction."""

    def __init__(self, max_sessions: int, idle_ttl_seconds: int) -> None:
        super().__init__()
        if max_sessions < 1 or idle_ttl_seconds < 1:
            raise ValueError("Session capacity and idle TTL must be positive.")
        self.max_sessions = max_sessions
        self.idle_ttl_seconds = idle_ttl_seconds

    def _evict(self, now: float) -> None:
        expired = [
            key
            for key, session in self._storage.items()
            if now - session.last_active > self.idle_ttl_seconds
        ]
        for key in expired:
            self._storage.pop(key, None)

        overflow = len(self._storage) - self.max_sessions
        if overflow > 0:
            oldest = sorted(self._storage.items(), key=lambda item: item[1].last_active)
            for key, _session in oldest[:overflow]:
                self._storage.pop(key, None)

    async def get(self, platform_key: str) -> SessionModel | None:
        self._evict(time.time())
        return await super().get(platform_key)

    async def set(self, platform_key: str, session: SessionModel) -> None:
        await super().set(platform_key, session)
        self._evict(time.time())


class BoundedInMemorySessionService(InMemorySessionService):
    """ADK session service that physically bounds events and active sessions."""

    def __init__(
        self,
        max_messages: int,
        max_sessions: int,
        idle_ttl_seconds: int,
    ) -> None:
        super().__init__()
        if max_messages < 1 or max_sessions < 1 or idle_ttl_seconds < 1:
            raise ValueError("History, session capacity, and idle TTL must be positive.")
        self.max_messages = max_messages
        self.max_sessions = max_sessions
        self.idle_ttl_seconds = idle_ttl_seconds

    def _all_sessions(self) -> list[tuple[str, str, str, Session]]:
        return [
            (app_name, user_id, session_id, session)
            for app_name, users in self.sessions.items()
            for user_id, user_sessions in users.items()
            for session_id, session in user_sessions.items()
        ]

    def _delete_stored_session(self, app_name: str, user_id: str, session_id: str) -> None:
        user_sessions = self.sessions.get(app_name, {}).get(user_id, {})
        user_sessions.pop(session_id, None)
        if not user_sessions:
            self.sessions.get(app_name, {}).pop(user_id, None)
            app_user_state = self.user_state.get(app_name, {})
            app_user_state.pop(user_id, None)
            if not app_user_state:
                self.user_state.pop(app_name, None)
        if not self.sessions.get(app_name):
            self.sessions.pop(app_name, None)

    def _evict(self, now: float) -> None:
        stored = self._all_sessions()
        for app_name, user_id, session_id, session in stored:
            if now - session.last_update_time > self.idle_ttl_seconds:
                self._delete_stored_session(app_name, user_id, session_id)

        stored = self._all_sessions()
        overflow = len(stored) - self.max_sessions
        if overflow > 0:
            oldest = sorted(stored, key=lambda item: item[3].last_update_time)
            for app_name, user_id, session_id, _session in oldest[:overflow]:
                self._delete_stored_session(app_name, user_id, session_id)

    async def create_session(self, **kwargs) -> Session:
        self._evict(time.time())
        session = await super().create_session(**kwargs)
        self._evict(time.time())
        return session

    async def get_session(self, **kwargs) -> Session | None:
        self._evict(time.time())
        return await super().get_session(**kwargs)

    async def append_event(self, session: Session, event: Event) -> Event:
        appended = await super().append_event(session, event)
        session.events = recent_session_events(session.events, self.max_messages)
        stored = self.sessions[session.app_name][session.user_id][session.id]
        stored.events = recent_session_events(stored.events, self.max_messages)
        return appended
