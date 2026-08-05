from __future__ import annotations

from google.adk.models.llm_request import LlmRequest
from google.genai import types

from app.history import limit_model_history, recent_chat_contents


def text_content(role: str, text: str) -> types.Content:
    return types.Content(role=role, parts=[types.Part(text=text)])


def test_recent_chat_contents_keeps_only_latest_ten_visible_messages() -> None:
    contents = [
        text_content("user" if index % 2 == 0 else "model", f"message-{index}")
        for index in range(14)
    ]

    result = recent_chat_contents(contents, max_messages=10)

    assert [content.parts[0].text for content in result] == [
        f"message-{index}" for index in range(4, 14)
    ]


def test_tool_context_inside_retained_window_is_preserved_without_counting_as_messages() -> None:
    visible_history = [
        text_content("user" if index % 2 == 0 else "model", f"message-{index}")
        for index in range(10)
    ]
    function_call = types.Content(
        role="model",
        parts=[
            types.Part(
                function_call=types.FunctionCall(id="call-1", name="analyze_operations", args={})
            )
        ],
    )
    function_response = types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    id="call-1",
                    name="analyze_operations",
                    response={"orders": 100},
                )
            )
        ],
    )
    contents = [text_content("user", "discard-me"), *visible_history]
    contents[4:4] = [function_call, function_response]

    result = recent_chat_contents(contents, max_messages=10)

    assert text_content("user", "discard-me") not in result
    assert function_call in result
    assert function_response in result
    assert sum(content.parts[0].text is not None for content in result) == 10


def test_history_callback_mutates_request_without_short_circuiting_model() -> None:
    request = LlmRequest(
        contents=[text_content("user", f"message-{index}") for index in range(12)]
    )
    callback = limit_model_history(10)

    response = callback(None, request)  # type: ignore[arg-type]

    assert response is None
    assert [content.parts[0].text for content in request.contents] == [
        f"message-{index}" for index in range(2, 12)
    ]


def test_short_history_is_returned_unchanged() -> None:
    contents = [text_content("user", "one"), text_content("model", "two")]

    assert recent_chat_contents(contents, max_messages=10) is contents
