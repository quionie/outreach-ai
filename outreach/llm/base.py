"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    provider: str
    tokens_used: int | None = None


class BaseLLM(ABC):
    """Abstract base class that all LLM providers must implement."""

    @abstractmethod
    def generate(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.7
    ) -> LLMResponse:
        """Generate a completion from the LLM.

        Args:
            system_prompt: System-level instructions for the model.
            user_prompt: The user's message/request.
            temperature: Sampling temperature (0.0 - 1.0).

        Returns:
            An LLMResponse with the generated content.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and reachable.

        Returns:
            True if the provider can be used, False otherwise.
        """
