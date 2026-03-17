"""Tests for the email channel module."""

from outreach.llm.base import BaseLLM, LLMResponse
from outreach.channels.email import generate_email_sequence
from outreach.tone import load_tone


class MockLLM(BaseLLM):
    """Mock LLM for testing."""

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> LLMResponse:
        return LLMResponse(
            content="# Mock Email Sequence\n\n## Step 1\nTest content",
            model="mock",
            provider="mock",
            tokens_used=100,
        )

    def is_available(self) -> bool:
        return True


def test_generate_email_sequence():
    llm = MockLLM()
    tone = load_tone("professional")

    response = generate_email_sequence(
        llm=llm,
        name="Test User",
        company="TestCo",
        role="CTO",
        product="TestProduct",
        value_prop="Save time",
        tone=tone,
    )

    assert response.content is not None
    assert len(response.content) > 0
    assert response.provider == "mock"


def test_generate_with_personalization():
    llm = MockLLM()
    tone = load_tone("professional")

    response = generate_email_sequence(
        llm=llm,
        name="Test User",
        company="TestCo",
        role="CTO",
        product="TestProduct",
        value_prop="Save time",
        tone=tone,
        personalization="Active on LinkedIn, recently promoted",
    )

    assert response.content is not None


def test_generate_with_variants():
    llm = MockLLM()
    tone = load_tone("casual")

    response = generate_email_sequence(
        llm=llm,
        name="Test User",
        company="TestCo",
        role="CTO",
        product="TestProduct",
        value_prop="Save time",
        tone=tone,
        variants=2,
    )

    assert response.content is not None
