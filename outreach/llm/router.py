"""LLM provider router — selects the right provider based on config and flags."""

from __future__ import annotations

from typing import Any

from rich.console import Console

from ..config import get_provider_config
from .base import BaseLLM
from .claude import ClaudeLLM
from .ollama_llm import OllamaLLM
from .openai_llm import OpenAILLM

console = Console()

PROVIDERS: dict[str, type[BaseLLM]] = {
    "claude": ClaudeLLM,
    "openai": OpenAILLM,
    "ollama": OllamaLLM,
}

PROVIDER_ORDER = ["claude", "openai", "ollama"]


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    config: dict[str, Any] | None = None,
) -> BaseLLM:
    """Get an LLM instance based on provider preference and availability.

    Resolution order:
        1. Explicit --provider flag
        2. default_provider from config file
        3. Auto-detect: try Claude -> OpenAI -> Ollama

    Args:
        provider: Explicit provider name (claude, openai, ollama).
        model: Specific model override.
        config: Full config dict.

    Returns:
        A configured BaseLLM instance.

    Raises:
        click.ClickException: If no provider is available.
    """
    import click

    config = config or {}

    # 1. Explicit provider
    if provider:
        return _create_provider(provider, model, config)

    # 2. Config default
    default = config.get("default_provider")
    if default:
        return _create_provider(default, model, config)

    # 3. Auto-detect
    for name in PROVIDER_ORDER:
        try:
            llm = _create_provider(name, model, config)
            if llm.is_available():
                return llm
        except Exception:
            continue

    raise click.ClickException(
        "No LLM provider available. Set an API key or run [bold]outreach init[/bold] to configure.\n"
        "  • Claude: set ANTHROPIC_API_KEY\n"
        "  • OpenAI: set OPENAI_API_KEY\n"
        "  • Ollama: ensure ollama is running locally"
    )


def _create_provider(
    name: str, model: str | None, config: dict[str, Any]
) -> BaseLLM:
    """Create a provider instance by name."""
    import click

    name = name.lower()
    if name not in PROVIDERS:
        raise click.ClickException(
            f"Unknown provider '{name}'. Choose from: {', '.join(PROVIDERS)}"
        )

    provider_config = get_provider_config(config, name)
    if model:
        provider_config = {**provider_config, "model": model}

    cls = PROVIDERS[name]
    return cls.from_config(provider_config)
