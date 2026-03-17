"""Tests for the CLI module."""

from click.testing import CliRunner

from outreach.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "outreach-ai" in result.output


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_generate_missing_required():
    runner = CliRunner()
    result = runner.invoke(cli, ["generate"])
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_tones_list():
    runner = CliRunner()
    result = runner.invoke(cli, ["tones"])
    assert result.exit_code == 0
    assert "professional" in result.output


def test_tones_show():
    runner = CliRunner()
    result = runner.invoke(cli, ["tones", "show", "--name", "professional"])
    assert result.exit_code == 0
    assert "professional" in result.output.lower()
