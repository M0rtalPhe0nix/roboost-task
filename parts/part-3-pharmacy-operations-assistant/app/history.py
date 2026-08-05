"""Bound the visible chat history included in each model request."""

from __future__ import annotations

from collections.abc import Callable

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types


def is_visible_chat_message(content: types.Content) -> bool:
    """Return whether content represents a human-visible chat message."""

    return bool(
        content.role in {"user", "model"}
        and content.parts
        and any(part.text and not part.thought for part in content.parts)
    )


def recent_chat_contents(
    contents: list[types.Content], max_messages: int
) -> list[types.Content]:
    """Keep the latest visible messages and their subsequent tool context.

    Function-call and function-response contents do not count as chat messages. Once
    the oldest retained visible message is found, every later content item is preserved
    so tool call/response pairs inside the retained window remain intact.
    """

    if max_messages < 1:
        raise ValueError("max_messages must be at least 1.")

    visible_messages = 0
    for index in range(len(contents) - 1, -1, -1):
        if not is_visible_chat_message(contents[index]):
            continue
        visible_messages += 1
        if visible_messages == max_messages:
            return contents[index:]
    return contents


def limit_model_history(
    max_messages: int,
) -> Callable[[CallbackContext, LlmRequest], LlmResponse | None]:
    """Build an ADK callback that applies the configured model-context window."""

    if max_messages < 1:
        raise ValueError("max_messages must be at least 1.")

    def callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest,
    ) -> LlmResponse | None:
        del callback_context
        llm_request.contents = recent_chat_contents(llm_request.contents, max_messages)
        return None

    return callback
