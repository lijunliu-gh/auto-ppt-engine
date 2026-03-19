"""LLM provider abstraction — multi-model support.

Supports **all major LLM providers** through auto-detection or explicit config.

Quick setup by model family::

    # OpenAI / reasoning models (default)
    export OPENAI_API_KEY="sk-..."
    export OPENAI_MODEL="gpt-4.1-mini"       # or o3, o4-mini, codex-mini-latest

    # Anthropic Claude
    export ANTHROPIC_API_KEY="sk-ant-..."
    export OPENAI_MODEL="claude-sonnet-4-20250514"

    # Google Gemini
    export GOOGLE_API_KEY="..."
    export OPENAI_MODEL="gemini-2.5-pro"

    # Qwen (通义千问)
    export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
    export OPENAI_API_KEY="sk-..." && export OPENAI_MODEL="qwen-plus"

    # DeepSeek
    export OPENAI_BASE_URL="https://api.deepseek.com"
    export OPENAI_API_KEY="sk-..." && export OPENAI_MODEL="deepseek-chat"

    # GLM / Zhipu (智谱)
    export OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
    export OPENAI_API_KEY="..." && export OPENAI_MODEL="glm-4-plus"

    # MiniMax
    export OPENAI_BASE_URL="https://api.minimax.chat/v1"
    export OPENAI_API_KEY="..." && export OPENAI_MODEL="MiniMax-Text-01"

To add a custom provider, implement ``LLMProvider`` and pass it to
``execute_planning_flow``.
"""

from __future__ import annotations

import importlib
import logging
import os
from typing import Any, Protocol

logger = logging.getLogger("auto-ppt")


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class LLMProvider(Protocol):
    """Minimal interface every LLM backend must satisfy."""

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Return the raw text completion for the given prompts."""
        ...


# ---------------------------------------------------------------------------
# OpenAI-compatible (covers OpenAI, Qwen, DeepSeek, GLM, MiniMax, etc.)
# ---------------------------------------------------------------------------


class OpenAIProvider:
    """Provider backed by any OpenAI-compatible endpoint.

    Works with: gpt-4.1-mini, gpt-4o, qwen-plus, deepseek-chat, glm-4-plus,
    MiniMax-Text-01, and reasoning models (o1, o3, o4-mini, codex-mini-latest).
    """

    _REASONING_PREFIXES = ("o1", "o3", "o4", "codex")

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
                "OPENAI_API_KEY is not set. "
                "Use mock mode for offline testing or configure the API key."
            )
        self._client: Any = OpenAI(
            api_key=resolved_key,
            base_url=base_url or os.getenv("OPENAI_BASE_URL") or None,
        )
        self._model = model or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"

    def _is_reasoning_model(self) -> bool:
        return self._model.startswith(self._REASONING_PREFIXES)

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        logger.info("Requesting deck JSON from model=%s", self._model)
        reasoning = self._is_reasoning_model()

        instruction_role = "developer" if reasoning else "system"
        messages = [
            {"role": instruction_role, "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        params: dict[str, Any] = {
            "model": self._model,
            "response_format": {"type": "json_object"},
            "messages": messages,
        }

        if reasoning:
            effort = os.getenv("OPENAI_REASONING_EFFORT", "medium")
            params["reasoning_effort"] = effort
        else:
            params["temperature"] = 0.3

        response = self._client.chat.completions.create(**params)
        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise RuntimeError("Model returned no content.")
        return str(content)


# ---------------------------------------------------------------------------
# Anthropic Claude
# ---------------------------------------------------------------------------


class AnthropicProvider:
    """Provider backed by the Anthropic Messages API.

    Works with: claude-sonnet-4-20250514, claude-3.5-sonnet, claude-3-opus, etc.
    Requires ``pip install anthropic``.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        Anthropic = importlib.import_module("anthropic").Anthropic

        resolved_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. "
                "Use mock mode for offline testing or configure the API key."
            )
        self._client: Any = Anthropic(api_key=resolved_key)
        self._model = model or os.getenv("OPENAI_MODEL") or "claude-sonnet-4-20250514"

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        logger.info("Requesting deck JSON from model=%s", self._model)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = response.content[0].text if response.content else None
        if not content:
            raise RuntimeError("Model returned no content.")
        return str(content)


# ---------------------------------------------------------------------------
# Google Gemini
# ---------------------------------------------------------------------------


class GeminiProvider:
    """Provider backed by Google Generative AI (Gemini).

    Works with: gemini-2.5-pro, gemini-2.5-flash, gemini-2.0-flash, etc.
    Requires ``pip install google-generativeai``.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        genai = importlib.import_module("google.generativeai")

        resolved_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not resolved_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. "
                "Use mock mode for offline testing or configure the API key."
            )
        genai.configure(api_key=resolved_key)
        self._model_name = model or os.getenv("OPENAI_MODEL") or "gemini-2.5-pro"
        self._genai = genai

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        logger.info("Requesting deck JSON from model=%s", self._model_name)
        model = self._genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system_prompt,
            generation_config=self._genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.3,
            ),
        )
        response = model.generate_content(user_prompt)
        if not response.text:
            raise RuntimeError("Model returned no content.")
        return response.text


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------

_ANTHROPIC_PREFIXES = ("claude",)
_GEMINI_PREFIXES = ("gemini",)


def _detect_provider_class(model: str) -> type:
    """Pick the right provider class based on model name."""
    if model.startswith(_ANTHROPIC_PREFIXES):
        return AnthropicProvider
    if model.startswith(_GEMINI_PREFIXES):
        return GeminiProvider
    return OpenAIProvider


def get_default_provider() -> LLMProvider:
    """Return the best provider based on environment variables.

    Detection order:
    1. Read ``OPENAI_MODEL`` (or default ``gpt-4.1-mini``)
    2. If model starts with ``claude`` -> AnthropicProvider
    3. If model starts with ``gemini`` -> GeminiProvider
    4. Otherwise -> OpenAIProvider (works for OpenAI, Qwen, DeepSeek, GLM, MiniMax, etc.)
    """
    model = os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"
    cls = _detect_provider_class(model)
    logger.info("Auto-detected provider %s for model=%s", cls.__name__, model)
    return cls(model=model)
