"""LinkedIn DM sequence generator."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from ..llm.base import BaseLLM, LLMResponse
from ..tone import format_tone_rules

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "linkedin_dm.yml"


def generate_linkedin_sequence(
    llm: BaseLLM,
    name: str,
    company: str,
    role: str,
    product: str,
    value_prop: str,
    tone: dict[str, Any],
    personalization: str = "",
    variants: int = 1,
) -> LLMResponse:
    """Generate a 3-message LinkedIn DM sequence.

    Args:
        llm: The LLM provider to use.
        name: Prospect's name.
        company: Prospect's company.
        role: Prospect's role/title.
        product: Your product/service name.
        value_prop: One-line value proposition.
        tone: Parsed tone profile dict.
        personalization: Personalization notes string.
        variants: Number of A/B variants (1-3).

    Returns:
        LLMResponse with the generated LinkedIn sequence.
    """
    prompts = _load_prompts()
    tone_rules = format_tone_rules(tone)

    personalization_context = ""
    if personalization:
        personalization_context = f"PERSONALIZATION CONTEXT:\n{personalization}"

    system_prompt = prompts["system_prompt"].format(
        tone_rules=tone_rules,
        personalization_context=personalization_context,
    )

    variant_instruction = ""
    if variants > 1:
        variant_instruction = (
            f"Generate {variants} A/B variants for EACH message. "
            "Each variant should take a meaningfully different approach."
        )

    user_prompt = prompts["user_prompt_template"].format(
        name=name,
        company=company,
        role=role,
        product=product,
        value_prop=value_prop,
        personalization=personalization or "None provided",
        variant_instruction=variant_instruction,
    )

    return llm.generate(system_prompt, user_prompt)


def _load_prompts() -> dict[str, str]:
    """Load the LinkedIn DM prompt template."""
    with open(PROMPT_FILE) as f:
        return yaml.safe_load(f)
