"""LLM provider abstraction.

Supports OpenAI-compatible APIs out of the box.  To add a new provider,
implement ``LLMProvider`` and pass the instance to ``execute_planning_flow``.
"""

from __future__ import annotations

import importlib
import logging
import os
from typing import Any, Protocol

logger = logging.getLogger("auto-ppt")


class LLMProvider(Protocol):
    """Minimal interface every LLM backend must satisfy."""

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Return the raw text completion for the given prompts."""
        ...


class OpenAIProvider:
    """Provider backed by any OpenAI-compatible endpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        OpenAI = importlib.import_module("openai").OpenAI

        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Use mock mode for offline testing or configure the API key."
            )
        self._client: Any = OpenAI(
            api_key=resolved_key,
            base_url=base_url or os.getenv("OPENAI_BASE_URL") or None,
        )
        self._model = model or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        logger.info("Requesting deck JSON from model=%s", self._model)
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise RuntimeError("Model returned no content.")
        return str(content)


def get_default_provider() -> LLMProvider:
    """Return the default provider based on environment variables."""
    return OpenAIProvider()
