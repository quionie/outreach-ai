"""Tone profile manager — loads and formats tone profiles for prompt injection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Default tones directory (relative to project root)
BUILTIN_TONES_DIR = Path(__file__).parent.parent / "tones"


def load_tone(name: str, custom_dir: str | None = None) -> dict[str, Any]:
    """Load a tone profile by name.

    Searches custom directory first (if provided), then built-in tones.

    Args:
        name: The tone profile name (without .yml extension).
        custom_dir: Optional path to a directory with custom tone files.

    Returns:
        Parsed tone profile dict.

    Raises:
        FileNotFoundError: If the tone profile doesn't exist.
    """
    # Check custom directory first
    if custom_dir:
        custom_path = Path(custom_dir) / f"{name}.yml"
        if custom_path.is_file():
            return _load_yaml(custom_path)

    # Check built-in tones
    builtin_path = BUILTIN_TONES_DIR / f"{name}.yml"
    if builtin_path.is_file():
        return _load_yaml(builtin_path)

    available = list_tones(custom_dir)
    raise FileNotFoundError(
        f"Tone profile '{name}' not found. Available tones: {', '.join(available)}"
    )


def list_tones(custom_dir: str | None = None) -> list[str]:
    """List all available tone profile names.

    Args:
        custom_dir: Optional path to a directory with custom tone files.

    Returns:
        Sorted list of tone names.
    """
    tones: set[str] = set()

    if BUILTIN_TONES_DIR.is_dir():
        for f in BUILTIN_TONES_DIR.glob("*.yml"):
            tones.add(f.stem)

    if custom_dir:
        custom_path = Path(custom_dir)
        if custom_path.is_dir():
            for f in custom_path.glob("*.yml"):
                tones.add(f.stem)

    return sorted(tones)


def format_tone_rules(tone: dict[str, Any]) -> str:
    """Format a tone profile's rules into a string for prompt injection.

    Args:
        tone: A parsed tone profile dict.

    Returns:
        Formatted string with tone rules, examples, and anti-patterns.
    """
    parts = [f"TONE: {tone.get('name', 'unknown')} — {tone.get('description', '')}"]

    rules = tone.get("rules", [])
    if rules:
        parts.append("\nTone rules:")
        for rule in rules:
            parts.append(f"  - {rule}")

    examples = tone.get("example_phrases", [])
    if examples:
        parts.append("\nExample phrases to emulate:")
        for phrase in examples:
            parts.append(f"  - \"{phrase}\"")

    anti = tone.get("anti_patterns", [])
    if anti:
        parts.append("\nNEVER use these phrases or patterns:")
        for pattern in anti:
            parts.append(f"  - \"{pattern}\"")

    return "\n".join(parts)


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load and parse a YAML file."""
    with open(path) as f:
        return yaml.safe_load(f) or {}
