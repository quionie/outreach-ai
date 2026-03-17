# Contributing to outreach-ai

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/quionie/outreach-ai.git
cd outreach-ai
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting:

```bash
ruff check .
ruff format .
```

## Pull Requests

1. Fork the repo and create your branch from `main`
2. Add tests for any new functionality
3. Ensure `ruff check .` passes
4. Ensure `pytest` passes
5. Submit your PR with a clear description of the changes

## Reporting Issues

Use [GitHub Issues](https://github.com/quionie/outreach-ai/issues) to report bugs or request features. Include:

- Steps to reproduce
- Expected vs actual behavior
- Your Python version and OS

## Adding a New Channel

1. Create a new file in `outreach/channels/`
2. Create a matching prompt template in `outreach/prompts/`
3. Register the channel in `outreach/cli.py` and `outreach/batch.py`
4. Add tests

## Adding a New LLM Provider

1. Create a new file in `outreach/llm/` that extends `BaseLLM`
2. Add a `from_config` classmethod
3. Register in `outreach/llm/router.py`
4. Add tests
