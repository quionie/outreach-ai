# outreach-ai

**AI-powered cold outreach sequence generator — multi-channel, multi-LLM, hyper-personalized.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/quionie/outreach-ai?style=social)](https://github.com/quionie/outreach-ai)

Generate hyper-personalized cold outreach sequences across email, LinkedIn, and Twitter/X from a single CLI command. Supports Claude, OpenAI, and Ollama (local) as LLM backends.

---

## Why outreach-ai?

- **Multi-channel from one command** — Generate email sequences, LinkedIn DMs, and Twitter DMs simultaneously
- **Actually personalized** — Optional LinkedIn profile scraping feeds real prospect data into your outreach
- **Any LLM, your choice** — Claude, GPT-4o, or run fully local with Ollama. No vendor lock-in
- **Battle-tested prompts** — Prompt templates built on cold outreach best practices, not generic AI fluff
- **Bulk processing** — Feed a CSV of 100 prospects and get personalized sequences for all of them

---

## Features

- [x] Multi-step email sequences (4-step with strategy notes)
- [x] LinkedIn DM sequences (3-step with character limits)
- [x] Twitter/X DM sequences (2-step, short-form)
- [x] A/B variant generation (up to 3 variants per step)
- [x] Configurable tone profiles (professional, casual, founder, challenger)
- [x] CSV batch processing with concurrent requests
- [x] LinkedIn profile scraping for auto-personalization
- [x] Multiple LLM backends (Claude, OpenAI, Ollama)
- [x] Beautiful terminal output with Rich
- [x] Markdown and JSON output formats
- [ ] CRM integrations (HubSpot, Salesforce)
- [ ] Email sending via SMTP/SendGrid
- [ ] Chrome extension for LinkedIn
- [ ] Web dashboard

---

## Installation

```bash
pip install outreach-ai
```

Or install from source for development:

```bash
git clone https://github.com/quionie/outreach-ai.git
cd outreach-ai
pip install -e ".[dev]"
```

---

## Quick Start

### 1. Configure

```bash
outreach init
```

This creates a `.outreachai.yml` config file. Or just set your API key:

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### 2. Generate for a single prospect

```bash
outreach generate \
  --name "Sarah Chen" \
  --company "Stripe" \
  --role "VP of Engineering" \
  --product "DevOnboard" \
  --value-prop "Cut developer onboarding time by 40%" \
  --channels email,linkedin \
  --tone founder
```

### 3. Batch process a CSV

```bash
outreach batch \
  --input prospects.csv \
  --product "DevOnboard" \
  --value-prop "Cut developer onboarding time by 40%" \
  --channels email,linkedin,twitter \
  --concurrency 5
```

---

## CLI Reference

### `outreach generate`

Generate outreach for a single prospect.

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--name` | Yes | — | Prospect's name |
| `--company` | Yes | — | Prospect's company |
| `--role` | Yes | — | Prospect's role/title |
| `--product` | Yes | — | Your product/service name |
| `--value-prop` | Yes | — | One-line value proposition |
| `--linkedin` | No | — | LinkedIn URL for auto-personalization |
| `--channels` | No | `email` | Comma-separated: email, linkedin, twitter |
| `--tone` | No | `professional` | Tone profile name |
| `--variants` | No | `1` | A/B variants per step (1-3) |
| `--provider` | No | From config | LLM provider: claude, openai, ollama |
| `--model` | No | Provider default | Specific model override |
| `--output` | No | `./output` | Output directory |
| `--format` | No | `md` | Output format: md, json, both |

### `outreach batch`

Process a CSV of prospects.

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--input` | Yes | — | Path to prospect CSV |
| `--product` | Yes | — | Your product/service name |
| `--value-prop` | Yes | — | One-line value proposition |
| `--channels` | No | `email` | Comma-separated channels |
| `--tone` | No | `professional` | Tone profile name |
| `--variants` | No | `1` | A/B variants per step |
| `--provider` | No | From config | LLM provider |
| `--model` | No | Provider default | Model override |
| `--output` | No | `./output` | Output directory |
| `--concurrency` | No | `3` | Parallel requests |

### `outreach tones`

List available tone profiles.

### `outreach tones show --name <tone>`

Show details of a specific tone profile.

### `outreach init`

Interactive setup wizard to create `.outreachai.yml`.

---

## Supported LLM Providers

| Provider | Default Model | Env Variable | Notes |
|----------|--------------|--------------|-------|
| Claude | `claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` | Recommended — best at nuanced writing |
| OpenAI | `gpt-4o` | `OPENAI_API_KEY` | Great alternative |
| Ollama | `llama3.1` | — | Fully local, no API key needed |

---

## Channel Types

### Email (4-step sequence)
1. **Initial outreach** — personalized, insight-led cold email
2. **Follow-up 1** (Day 3) — value-add with a different angle
3. **Follow-up 2** (Day 5) — social proof / case study
4. **Breakup email** (Day 7) — graceful close

### LinkedIn (3-message sequence)
1. **Connection request** — under 300 characters, no pitch
2. **First message** — personalized value-add after connecting
3. **Follow-up** — soft CTA

### Twitter/X (2-message sequence)
1. **Ice-breaker** — ultra-short, reference something specific
2. **Value DM** — brief pitch with soft CTA

---

## Tone Profiles

Built-in tones: `professional`, `casual`, `founder`, `challenger`

```bash
# List all tones
outreach tones

# See tone details
outreach tones show --name challenger
```

### Custom Tones

Create a YAML file in your custom tones directory:

```yaml
name: my-tone
description: "My custom tone for SaaS founders"
rules:
  - Be direct and specific
  - Reference metrics and data
example_phrases:
  - "We helped 3 companies like yours..."
anti_patterns:
  - "Just touching base"
```

Set `custom_tones_dir` in `.outreachai.yml` to point to your directory.

---

## Batch Mode

### CSV Format

```csv
name,company,role,linkedin_url,notes
Sarah Chen,Stripe,VP of Engineering,https://linkedin.com/in/sarachen,Led developer platform team
Marcus Johnson,Notion,Head of Growth,,Previously at Figma
```

Required columns: `name`, `company`, `role`
Optional columns: `linkedin_url`, `notes`

---

## Configuration

Create `.outreachai.yml` in your project root (or run `outreach init`):

```yaml
default_provider: claude
default_model: null

providers:
  claude:
    api_key: ${ANTHROPIC_API_KEY}
  openai:
    api_key: ${OPENAI_API_KEY}
  ollama:
    host: http://localhost:11434
    model: llama3.1

defaults:
  channels: [email]
  tone: professional
  variants: 1
  output_format: md

custom_tones_dir: null
```

Environment variables are supported with `${VAR_NAME}` syntax.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT — see [LICENSE](LICENSE).

---

If you find this useful, give us a star! It helps others discover the project.
