"""Tests for the LLM router module."""

import pytest

from outreach.llm.claude import ClaudeLLM
from outreach.llm.openai_llm import OpenAILLM
from outreach.llm.ollama_llm import OllamaLLM
from outreach.llm.router import get_llm, _create_provider


def test_create_claude_provider():
    llm = _create_provider("claude", None, {"providers": {"claude": {"api_key": "test-key"}}})
    assert isinstance(llm, ClaudeLLM)
    assert llm.api_key == "test-key"


def test_create_openai_provider():
    llm = _create_provider("openai", None, {"providers": {"openai": {"api_key": "test-key"}}})
    assert isinstance(llm, OpenAILLM)
    assert llm.api_key == "test-key"


def test_create_ollama_provider():
    llm = _create_provider("ollama", None, {"providers": {"ollama": {"host": "http://localhost:11434"}}})
    assert isinstance(llm, OllamaLLM)


def test_create_provider_with_model_override():
    llm = _create_provider("claude", "claude-opus-4-20250514", {"providers": {"claude": {"api_key": "k"}}})
    assert isinstance(llm, ClaudeLLM)
    assert llm.model == "claude-opus-4-20250514"


def test_create_unknown_provider():
    import click
    with pytest.raises(click.ClickException, match="Unknown provider"):
        _create_provider("unknown", None, {})


def test_get_llm_explicit_provider():
    config = {"providers": {"claude": {"api_key": "test"}}}
    llm = get_llm(provider="claude", config=config)
    assert isinstance(llm, ClaudeLLM)


def test_get_llm_config_default():
    config = {"default_provider": "openai", "providers": {"openai": {"api_key": "test"}}}
    llm = get_llm(config=config)
    assert isinstance(llm, OpenAILLM)
