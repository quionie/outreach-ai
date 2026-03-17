"""CSV batch processing engine for bulk prospect outreach."""

from __future__ import annotations

import csv
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .channels.email import generate_email_sequence
from .channels.linkedin import generate_linkedin_sequence
from .channels.twitter import generate_twitter_sequence
from .llm.base import BaseLLM
from .personalization.linkedin_scraper import scrape_linkedin_profile
from .tone import load_tone

logger = logging.getLogger(__name__)
console = Console()

REQUIRED_COLUMNS = {"name", "company", "role"}
OPTIONAL_COLUMNS = {"linkedin_url", "notes"}

CHANNEL_GENERATORS = {
    "email": generate_email_sequence,
    "linkedin": generate_linkedin_sequence,
    "twitter": generate_twitter_sequence,
}


@dataclass
class ProspectResult:
    """Result of processing a single prospect."""

    name: str
    company: str
    channels_generated: list[str] = field(default_factory=list)
    output_path: str = ""
    error: str | None = None


def validate_csv(filepath: str | Path) -> list[dict[str, str]]:
    """Read and validate a prospect CSV file.

    Args:
        filepath: Path to the CSV file.

    Returns:
        List of prospect dicts.

    Raises:
        click.ClickException: If the CSV is invalid or missing required columns.
    """
    import click

    path = Path(filepath)
    if not path.is_file():
        raise click.ClickException(f"CSV file not found: {filepath}")

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise click.ClickException("CSV file is empty or has no headers.")

        headers = {h.strip().lower() for h in reader.fieldnames}
        missing = REQUIRED_COLUMNS - headers
        if missing:
            raise click.ClickException(
                f"CSV missing required columns: {', '.join(sorted(missing))}. "
                f"Required: {', '.join(sorted(REQUIRED_COLUMNS))}"
            )

        rows = []
        for i, row in enumerate(reader, start=2):
            # Normalize keys to lowercase
            normalized = {k.strip().lower(): v.strip() for k, v in row.items() if v}
            if not normalized.get("name") or not normalized.get("company") or not normalized.get("role"):
                logger.warning(f"Row {i}: missing required field(s), skipping.")
                continue
            rows.append(normalized)

    if not rows:
        raise click.ClickException("CSV has no valid prospect rows.")

    return rows


def process_batch(
    csv_path: str | Path,
    llm: BaseLLM,
    channels: list[str],
    tone_name: str,
    product: str,
    value_prop: str,
    variants: int = 1,
    output_dir: str = "./output",
    concurrency: int = 3,
    custom_tones_dir: str | None = None,
) -> list[ProspectResult]:
    """Process a CSV of prospects in batch.

    Args:
        csv_path: Path to the prospect CSV.
        llm: The LLM provider to use.
        channels: List of channels to generate (email, linkedin, twitter).
        tone_name: Name of the tone profile.
        product: Your product/service name.
        value_prop: Your value proposition.
        variants: Number of A/B variants.
        output_dir: Directory for output files.
        concurrency: Max parallel requests.
        custom_tones_dir: Optional custom tones directory.

    Returns:
        List of ProspectResult for each prospect.
    """
    prospects = validate_csv(csv_path)
    tone = load_tone(tone_name, custom_tones_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    results: list[ProspectResult] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing prospects...", total=len(prospects))

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {
                executor.submit(
                    _process_single_prospect,
                    prospect=prospect,
                    llm=llm,
                    channels=channels,
                    tone=tone,
                    product=product,
                    value_prop=value_prop,
                    variants=variants,
                    output_dir=out_path,
                ): prospect
                for prospect in prospects
            }

            for future in as_completed(futures):
                prospect = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process {prospect.get('name', '?')}: {e}")
                    results.append(ProspectResult(
                        name=prospect.get("name", "Unknown"),
                        company=prospect.get("company", "Unknown"),
                        error=str(e),
                    ))
                progress.advance(task)

    # Write summary JSON
    summary_path = out_path / "batch_summary.json"
    with open(summary_path, "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)

    return results


def _process_single_prospect(
    prospect: dict[str, str],
    llm: BaseLLM,
    channels: list[str],
    tone: dict[str, Any],
    product: str,
    value_prop: str,
    variants: int,
    output_dir: Path,
) -> ProspectResult:
    """Process a single prospect across all channels."""
    name = prospect["name"]
    company = prospect["company"]
    role = prospect["role"]
    linkedin_url = prospect.get("linkedin_url", "")
    notes = prospect.get("notes", "")

    # Build personalization
    personalization = notes
    if linkedin_url:
        profile = scrape_linkedin_profile(linkedin_url)
        profile_data = profile.to_personalization_string()
        if profile_data != "No LinkedIn data available.":
            personalization = f"{profile_data}\n\nAdditional notes: {notes}" if notes else profile_data

    # Create prospect output directory
    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in name).strip().replace(" ", "_")
    prospect_dir = output_dir / safe_name
    prospect_dir.mkdir(parents=True, exist_ok=True)

    generated_channels = []

    for channel in channels:
        generator = CHANNEL_GENERATORS.get(channel)
        if not generator:
            logger.warning(f"Unknown channel '{channel}', skipping.")
            continue

        response = generator(
            llm=llm,
            name=name,
            company=company,
            role=role,
            product=product,
            value_prop=value_prop,
            tone=tone,
            personalization=personalization,
            variants=variants,
        )

        # Write markdown output
        output_file = prospect_dir / f"{channel}.md"
        output_file.write_text(response.content)
        generated_channels.append(channel)

    return ProspectResult(
        name=name,
        company=company,
        channels_generated=generated_channels,
        output_path=str(prospect_dir),
    )
