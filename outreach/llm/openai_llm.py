"""OpenAI LLM provider."""

from __future__ import annotations

import os
from typing import Any

from .base import BaseLLM, LLMResponse

DEFAULT_MODEL = "gpt-4o"


class OpenAILLM(BaseLLM):
    """LLM provider using OpenAI's API."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model or DEFAULT_MODEL

    def generate(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.7
    ) -> LLMResponse:
        """Generate a completion using OpenAI."""
        import openai

        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else None

        return LLMResponse(
            content=content,
            model=self.model,
            provider="openai",
            tokens_used=tokens,
        )

    def is_available(self) -> bool:
        """Check if the OpenAI API key is configured."""
        return bool(self.api_key)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> OpenAILLM:
        """Create an OpenAILLM from a provider config dict."""
        return cls(api_key=config.get("api_key"), model=config.get("model"))
