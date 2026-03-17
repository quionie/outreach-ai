"""Configuration loading and management for outreach-ai."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

console = Console()

DEFAULT_CONFIG_FILENAME = ".outreachai.yml"
ENV_VAR_PATTERN = re.compile(r"\$\{(\w+)\}")


def _resolve_env_vars(value: Any) -> Any:
    """Recursively resolve ${ENV_VAR} references in config values."""
    if isinstance(value, str):
        def _replace(match: re.Match) -> str:
            env_name = match.group(1)
            return os.environ.get(env_name, "")
        return ENV_VAR_PATTERN.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


def find_config_file() -> Path | None:
    """Search for .outreachai.yml in CWD and parent directories."""
    current = Path.cwd()
    for directory in [current, *current.parents]:
        config_path = directory / DEFAULT_CONFIG_FILENAME
        if config_path.is_file():
            return config_path
    return None


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and return the outreach-ai configuration.

    Args:
        config_path: Explicit path to config file. If None, searches
            CWD and parent directories.

    Returns:
        Parsed config dict with env vars resolved. Returns default
        config if no file is found.
    """
    if config_path is not None:
        path = Path(config_path)
    else:
        path = find_config_file()

    if path is None or not path.is_file():
        return default_config()

    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    return _resolve_env_vars(raw)


def default_config() -> dict[str, Any]:
    """Return the default configuration."""
    return {
        "default_provider": None,
        "default_model": None,
        "providers": {
            "claude": {"api_key": os.environ.get("ANTHROPIC_API_KEY", "")},
            "openai": {"api_key": os.environ.get("OPENAI_API_KEY", "")},
            "ollama": {"host": "http://localhost:11434", "model": "llama3.1"},
        },
        "defaults": {
            "channels": ["email"],
            "tone": "professional",
            "variants": 1,
            "output_format": "md",
        },
        "custom_tones_dir": None,
    }


def get_provider_config(config: dict[str, Any], provider: str) -> dict[str, Any]:
    """Get configuration for a specific LLM provider.

    Args:
        config: The full config dict.
        provider: Provider name (claude, openai, ollama).

    Returns:
        Provider-specific config dict.
    """
    return config.get("providers", {}).get(provider, {})


def get_default(config: dict[str, Any], key: str) -> Any:
    """Get a default value from config.

    Args:
        config: The full config dict.
        key: The default key to look up.

    Returns:
        The default value, or None if not found.
    """
    return config.get("defaults", {}).get(key)
