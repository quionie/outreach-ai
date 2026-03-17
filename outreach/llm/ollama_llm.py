"""Ollama (local) LLM provider."""

from __future__ import annotations

from typing import Any

import httpx

from .base import BaseLLM, LLMResponse

DEFAULT_MODEL = "llama3.1"
DEFAULT_HOST = "http://localhost:11434"


class OllamaLLM(BaseLLM):
    """LLM provider using a local Ollama instance."""

    def __init__(self, host: str | None = None, model: str | None = None) -> None:
        self.host = (host or DEFAULT_HOST).rstrip("/")
        self.model = model or DEFAULT_MODEL

    def generate(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.7
    ) -> LLMResponse:
        """Generate a completion using Ollama."""
        response = httpx.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "system": system_prompt,
                "prompt": user_prompt,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data.get("response", ""),
            model=self.model,
            provider="ollama",
            tokens_used=data.get("eval_count"),
        )

    def is_available(self) -> bool:
        """Check if Ollama is running and reachable."""
        try:
            resp = httpx.get(f"{self.host}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> OllamaLLM:
        """Create an OllamaLLM from a provider config dict."""
        return cls(host=config.get("host"), model=config.get("model"))
