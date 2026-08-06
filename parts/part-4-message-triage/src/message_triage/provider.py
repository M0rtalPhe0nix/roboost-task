from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from .budget import TokenUsage
from .models import Intent, ModelDecision
from .prompt import RESPONSE_SCHEMA


@dataclass(frozen=True)
class ProviderResponse:
    decisions: tuple[ModelDecision, ...]
    usage: TokenUsage
    response_id: str | None = None
    model_version: str | None = None


class ProviderResponseError(RuntimeError):
    """A billed provider response could not be accepted by the classifier."""

    def __init__(
        self,
        message: str,
        usage: TokenUsage,
        *,
        response_id: str | None = None,
        model_version: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.usage = usage
        self.response_id = response_id
        self.model_version = model_version
        self.retryable = retryable


class TriageProvider(Protocol):
    def classify(self, prompt: str, *, max_output_tokens: int) -> ProviderResponse: ...


class GeminiProvider:
    def __init__(self, api_key: str, model: str = "gemini-3.5-flash-lite") -> None:
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "Gemini support is not installed; run `pip install -e '.[gemini]'`"
            ) from exc
        self._client = genai.Client(api_key=api_key)
        self.model = model

    def classify(self, prompt: str, *, max_output_tokens: int) -> ProviderResponse:
        from google.genai import types

        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json",
                response_json_schema=RESPONSE_SCHEMA,
            ),
        )
        usage = _parse_usage(response.usage_metadata)
        response_id = getattr(response, "response_id", None)
        model_version = getattr(response, "model_version", None)
        if not response.text:
            raise ProviderResponseError(
                "Gemini returned no response text; billed usage was recorded",
                usage,
                response_id=response_id,
                model_version=model_version,
            )
        try:
            payload = json.loads(response.text)
            decisions = _parse_decisions(payload)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            finish_reason = _finish_reason(response)
            raise ProviderResponseError(
                "Gemini returned invalid or truncated structured output "
                f"(finish_reason={finish_reason}); billed usage was recorded",
                usage,
                response_id=response_id,
                model_version=model_version,
                retryable="MAX_TOKENS" in finish_reason,
            ) from exc
        return ProviderResponse(
            decisions=decisions,
            usage=usage,
            response_id=response_id,
            model_version=model_version,
        )


def _parse_decisions(payload: Any) -> tuple[ModelDecision, ...]:
    if not isinstance(payload, dict) or set(payload) != {"id", "i", "u"}:
        raise ValueError("provider response must contain id, i, and u arrays")
    ids, intents, urgent_flags = payload["id"], payload["i"], payload["u"]
    if not all(isinstance(values, list) for values in (ids, intents, urgent_flags)):
        raise ValueError("provider response fields must be arrays")
    if len(ids) != len(intents) or len(ids) != len(urgent_flags):
        raise ValueError("provider response arrays must have equal lengths")
    decisions = []
    for message_id, intent, is_urgent in zip(ids, intents, urgent_flags, strict=True):
        if not isinstance(message_id, str) or not isinstance(is_urgent, bool):
            raise ValueError("provider decision has invalid field types")
        decisions.append(ModelDecision(message_id, Intent(intent), is_urgent))
    return tuple(decisions)


def _parse_usage(metadata: Any) -> TokenUsage:
    if metadata is None:
        raise RuntimeError("Gemini response is missing usage metadata")
    prompt_tokens = int(getattr(metadata, "prompt_token_count", 0) or 0)
    candidate_tokens = int(getattr(metadata, "candidates_token_count", 0) or 0)
    thought_tokens = int(getattr(metadata, "thoughts_token_count", 0) or 0)
    total_tokens = int(getattr(metadata, "total_token_count", 0) or 0)
    if prompt_tokens <= 0 or total_tokens <= 0:
        raise RuntimeError("Gemini response contains invalid usage metadata")
    return TokenUsage(
        input_tokens=prompt_tokens,
        output_tokens=candidate_tokens + thought_tokens,
        candidate_tokens=candidate_tokens,
        thought_tokens=thought_tokens,
        total_tokens=total_tokens,
    )


def _finish_reason(response: Any) -> str:
    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        return "unknown"
    reason = getattr(candidates[0], "finish_reason", None)
    return str(reason or "unknown")
