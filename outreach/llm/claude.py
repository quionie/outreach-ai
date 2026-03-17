"""Anthropic Claude LLM provider."""

from __future__ import annotations

import os
from typing import Any

from .base import BaseLLM, LLMResponse

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class ClaudeLLM(BaseLLM):
    """LLM provider using Anthropic's Claude API."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model or DEFAULT_MODEL

    def generate(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.7
    ) -> LLMResponse:
        """Generate a completion using Claude."""
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = response.content[0].text
        tokens = (response.usage.input_tokens or 0) + (response.usage.output_tokens or 0)

        return LLMResponse(
            content=content,
            model=self.model,
            provider="claude",
            tokens_used=tokens,
        )

    def is_available(self) -> bool:
        """Check if the Anthropic API key is configured."""
        return bool(self.api_key)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ClaudeLLM:
        """Create a ClaudeLLM from a provider config dict."""
        return cls(api_key=config.get("api_key"), model=config.get("model"))
