"""CLI entry point for outreach-ai."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .batch import process_batch
from .channels.email import generate_email_sequence
from .channels.linkedin import generate_linkedin_sequence
from .channels.twitter import generate_twitter_sequence
from .config import load_config, get_default, DEFAULT_CONFIG_FILENAME
from .llm.router import get_llm
from .personalization.linkedin_scraper import scrape_linkedin_profile
from .tone import format_tone_rules, list_tones, load_tone

console = Console()

CHANNEL_GENERATORS = {
    "email": generate_email_sequence,
    "linkedin": generate_linkedin_sequence,
    "twitter": generate_twitter_sequence,
}


@click.group()
@click.version_option(__version__, prog_name="outreach-ai")
@click.option("--verbose", is_flag=True, help="Enable verbose logging.")
def cli(verbose: bool) -> None:
    """outreach-ai — AI-powered cold outreach sequence generator."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


@cli.command()
@click.option("--name", required=True, help="Prospect's name.")
@click.option("--company", required=True, help="Prospect's company.")
@click.option("--role", required=True, help="Prospect's role/title.")
@click.option("--linkedin", default=None, help="LinkedIn profile URL for auto-personalization.")
@click.option("--channels", default=None, help="Comma-separated channels: email,linkedin,twitter")
@click.option("--tone", "tone_name", default=None, help="Tone profile name (default: professional).")
@click.option("--variants", default=None, type=int, help="A/B variants per step (1-3).")
@click.option("--provider", default=None, help="LLM provider: claude, openai, ollama.")
@click.option("--model", default=None, help="Specific model override.")
@click.option("--product", required=True, help="Your product/service name.")
@click.option("--value-prop", required=True, help="One-line value proposition.")
@click.option("--output", "output_dir", default="./output", help="Output directory.")
@click.option("--format", "output_format", default=None, help="Output format: md, json, both.")
def generate(
    name: str,
    company: str,
    role: str,
    linkedin: str | None,
    channels: str | None,
    tone_name: str | None,
    variants: int | None,
    provider: str | None,
    model: str | None,
    product: str,
    value_prop: str,
    output_dir: str,
    output_format: str | None,
) -> None:
    """Generate outreach sequences for a single prospect."""
    config = load_config()

    # Resolve defaults from config
    channel_list = (channels or ",".join(get_default(config, "channels") or ["email"])).split(",")
    channel_list = [c.strip().lower() for c in channel_list]
    tone_name = tone_name or get_default(config, "tone") or "professional"
    variants = variants or get_default(config, "variants") or 1
    output_format = output_format or get_default(config, "output_format") or "md"

    if variants < 1 or variants > 3:
        raise click.ClickException("Variants must be between 1 and 3.")

    # Validate channels
    for ch in channel_list:
        if ch not in CHANNEL_GENERATORS:
            raise click.ClickException(
                f"Unknown channel '{ch}'. Choose from: {', '.join(CHANNEL_GENERATORS)}"
            )

    # Load tone
    custom_tones_dir = config.get("custom_tones_dir")
    try:
        tone = load_tone(tone_name, custom_tones_dir)
    except FileNotFoundError as e:
        raise click.ClickException(str(e))

    # Get LLM
    llm = get_llm(provider=provider, model=model, config=config)

    console.print(Panel(
        f"[bold]Prospect:[/bold] {name}, {role} at {company}\n"
        f"[bold]Channels:[/bold] {', '.join(channel_list)}\n"
        f"[bold]Tone:[/bold] {tone_name} | [bold]Variants:[/bold] {variants}\n"
        f"[bold]Provider:[/bold] {llm.__class__.__name__}",
        title="outreach-ai",
        border_style="blue",
    ))

    # Personalization
    personalization = ""
    if linkedin:
        with console.status("[bold blue]Scraping LinkedIn profile..."):
            profile = scrape_linkedin_profile(linkedin)
            personalization = profile.to_personalization_string()
            if personalization != "No LinkedIn data available.":
                console.print("[green]LinkedIn data loaded.[/green]")
            else:
                console.print("[yellow]Could not fetch LinkedIn data. Using provided info only.[/yellow]")

    # Generate for each channel
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    results_table = Table(title="Generation Results")
    results_table.add_column("Channel", style="cyan")
    results_table.add_column("Status", style="green")
    results_table.add_column("Output", style="dim")

    for channel in channel_list:
        generator = CHANNEL_GENERATORS[channel]

        with console.status(f"[bold blue]Generating {channel} sequence..."):
            try:
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
            except Exception as e:
                console.print(f"[red]Error generating {channel}: {e}[/red]")
                results_table.add_row(channel, "[red]Failed[/red]", str(e))
                continue

        # Write output
        if output_format in ("md", "both"):
            md_file = out_path / f"{channel}_sequence.md"
            md_file.write_text(response.content)

        if output_format in ("json", "both"):
            json_file = out_path / f"{channel}_sequence.json"
            json_file.write_text(json.dumps({
                "channel": channel,
                "prospect": {"name": name, "company": company, "role": role},
                "product": product,
                "value_prop": value_prop,
                "tone": tone_name,
                "variants": variants,
                "content": response.content,
                "model": response.model,
                "provider": response.provider,
                "tokens_used": response.tokens_used,
            }, indent=2))

        output_files = []
        if output_format in ("md", "both"):
            output_files.append(f"{channel}_sequence.md")
        if output_format in ("json", "both"):
            output_files.append(f"{channel}_sequence.json")

        results_table.add_row(channel, "Done", ", ".join(output_files))

        # Display the generated content
        console.print()
        console.print(Panel(
            response.content,
            title=f"{channel.title()} Sequence",
            border_style="green",
        ))

    console.print()
    console.print(results_table)
    console.print(f"\n[dim]Output saved to: {out_path.resolve()}[/dim]")


@cli.command()
@click.option("--input", "csv_path", required=True, help="Path to prospect CSV file.")
@click.option("--channels", default=None, help="Comma-separated channels: email,linkedin,twitter")
@click.option("--tone", "tone_name", default=None, help="Tone profile name.")
@click.option("--variants", default=None, type=int, help="A/B variants per step (1-3).")
@click.option("--provider", default=None, help="LLM provider: claude, openai, ollama.")
@click.option("--model", default=None, help="Specific model override.")
@click.option("--product", required=True, help="Your product/service name.")
@click.option("--value-prop", required=True, help="One-line value proposition.")
@click.option("--output", "output_dir", default="./output", help="Output directory.")
@click.option("--concurrency", default=3, type=int, help="Parallel requests (default: 3).")
def batch(
    csv_path: str,
    channels: str | None,
    tone_name: str | None,
    variants: int | None,
    provider: str | None,
    model: str | None,
    product: str,
    value_prop: str,
    output_dir: str,
    concurrency: int,
) -> None:
    """Process a CSV of prospects in batch."""
    config = load_config()

    channel_list = (channels or ",".join(get_default(config, "channels") or ["email"])).split(",")
    channel_list = [c.strip().lower() for c in channel_list]
    tone_name = tone_name or get_default(config, "tone") or "professional"
    variants = variants or get_default(config, "variants") or 1
    custom_tones_dir = config.get("custom_tones_dir")

    llm = get_llm(provider=provider, model=model, config=config)

    console.print(Panel(
        f"[bold]CSV:[/bold] {csv_path}\n"
        f"[bold]Channels:[/bold] {', '.join(channel_list)}\n"
        f"[bold]Tone:[/bold] {tone_name} | [bold]Variants:[/bold] {variants}\n"
        f"[bold]Concurrency:[/bold] {concurrency}\n"
        f"[bold]Provider:[/bold] {llm.__class__.__name__}",
        title="outreach-ai batch",
        border_style="blue",
    ))

    results = process_batch(
        csv_path=csv_path,
        llm=llm,
        channels=channel_list,
        tone_name=tone_name,
        product=product,
        value_prop=value_prop,
        variants=variants,
        output_dir=output_dir,
        concurrency=concurrency,
        custom_tones_dir=custom_tones_dir,
    )

    # Summary table
    table = Table(title="Batch Results")
    table.add_column("Prospect", style="cyan")
    table.add_column("Company", style="dim")
    table.add_column("Channels", style="green")
    table.add_column("Status")
    table.add_column("Output", style="dim")

    for r in results:
        status = "[green]Done[/green]" if not r.error else f"[red]{r.error}[/red]"
        table.add_row(
            r.name,
            r.company,
            ", ".join(r.channels_generated) if r.channels_generated else "-",
            status,
            r.output_path or "-",
        )

    console.print()
    console.print(table)
    console.print(f"\n[dim]Summary saved to: {Path(output_dir).resolve() / 'batch_summary.json'}[/dim]")


@cli.group(invoke_without_command=True)
@click.pass_context
def tones(ctx: click.Context) -> None:
    """List available tone profiles."""
    if ctx.invoked_subcommand is not None:
        return

    config = load_config()
    custom_dir = config.get("custom_tones_dir")
    available = list_tones(custom_dir)

    table = Table(title="Available Tone Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Description")

    for name in available:
        try:
            tone = load_tone(name, custom_dir)
            table.add_row(name, tone.get("description", ""))
        except FileNotFoundError:
            table.add_row(name, "[dim]Could not load[/dim]")

    console.print(table)


@tones.command("show")
@click.option("--name", required=True, help="Tone profile name.")
def tones_show(name: str) -> None:
    """Show details of a specific tone profile."""
    config = load_config()
    custom_dir = config.get("custom_tones_dir")

    try:
        tone = load_tone(name, custom_dir)
    except FileNotFoundError as e:
        raise click.ClickException(str(e))

    console.print(Panel(
        format_tone_rules(tone),
        title=f"Tone: {name}",
        border_style="blue",
    ))


@cli.command()
def init() -> None:
    """Interactive setup — creates .outreachai.yml config file."""
    config_path = Path.cwd() / DEFAULT_CONFIG_FILENAME

    if config_path.exists():
        if not click.confirm(f"{DEFAULT_CONFIG_FILENAME} already exists. Overwrite?"):
            console.print("[yellow]Aborted.[/yellow]")
            return

    console.print(Panel(
        "Let's set up outreach-ai! I'll walk you through the configuration.",
        title="outreach-ai setup",
        border_style="blue",
    ))

    # Provider selection
    provider = click.prompt(
        "Default LLM provider",
        type=click.Choice(["claude", "openai", "ollama"]),
        default="claude",
    )

    config_data: dict = {
        "default_provider": provider,
        "default_model": None,
        "providers": {
            "claude": {"api_key": "${ANTHROPIC_API_KEY}"},
            "openai": {"api_key": "${OPENAI_API_KEY}"},
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

    # API key setup
    if provider in ("claude", "openai"):
        env_var = "ANTHROPIC_API_KEY" if provider == "claude" else "OPENAI_API_KEY"
        console.print(f"\n[dim]Set your API key via the {env_var} environment variable,[/dim]")
        console.print(f"[dim]or enter it below (it will be stored in {DEFAULT_CONFIG_FILENAME}).[/dim]")

        api_key = click.prompt(
            f"API key (or press Enter to use ${{{env_var}}})",
            default=f"${{{env_var}}}",
            show_default=False,
        )
        config_data["providers"][provider]["api_key"] = api_key

    # Default channels
    default_channels = click.prompt(
        "Default channels (comma-separated)",
        default="email",
    )
    config_data["defaults"]["channels"] = [c.strip() for c in default_channels.split(",")]

    # Default tone
    available_tones = list_tones()
    default_tone = click.prompt(
        f"Default tone ({', '.join(available_tones)})",
        default="professional",
    )
    config_data["defaults"]["tone"] = default_tone

    # Write config
    import yaml
    with open(config_path, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    console.print(f"\n[green]Config saved to {config_path}[/green]")
    console.print("[dim]You're ready to go! Try:[/dim]")
    console.print('[bold]  outreach generate --name "Jane Doe" --company "Acme" '
                  '--role "CTO" --product "MyApp" --value-prop "Save 10hrs/week"[/bold]')


if __name__ == "__main__":
    cli()
