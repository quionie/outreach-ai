"""Tests for the batch processing module."""

import csv
import tempfile
from pathlib import Path

import pytest

from outreach.batch import validate_csv


def test_validate_csv_valid():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(["name", "company", "role", "linkedin_url", "notes"])
        writer.writerow(["Jane Doe", "Acme", "CTO", "", "Great prospect"])
        writer.writerow(["John Smith", "BigCo", "VP Sales", "", ""])
        f.flush()

        rows = validate_csv(f.name)
        assert len(rows) == 2
        assert rows[0]["name"] == "Jane Doe"
        assert rows[0]["company"] == "Acme"

    Path(f.name).unlink()


def test_validate_csv_missing_columns():
    import click

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(["name", "email"])
        writer.writerow(["Jane", "jane@test.com"])
        f.flush()

        with pytest.raises(click.ClickException, match="missing required columns"):
            validate_csv(f.name)

    Path(f.name).unlink()


def test_validate_csv_file_not_found():
    import click

    with pytest.raises(click.ClickException, match="not found"):
        validate_csv("/nonexistent/file.csv")


def test_validate_csv_skips_empty_rows():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(["name", "company", "role"])
        writer.writerow(["Jane Doe", "Acme", "CTO"])
        writer.writerow(["", "BigCo", "VP"])  # Missing name — should be skipped
        writer.writerow(["John", "BigCo", "VP Sales"])
        f.flush()

        rows = validate_csv(f.name)
        assert len(rows) == 2

    Path(f.name).unlink()
