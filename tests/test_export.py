"""Tests for envault.export."""

import json
import pytest

from envault.export import export, ExportError, SUPPORTED_FORMATS


SAMPLE = {
    "DB_PASSWORD": "s3cr3t",
    "API_KEY": "abc123",
    "GREETING": 'say "hello"',
}


# ---------------------------------------------------------------------------
# dotenv format
# ---------------------------------------------------------------------------

def test_dotenv_contains_all_keys():
    result = export(SAMPLE, "dotenv")
    for key in SAMPLE:
        assert key in result


def test_dotenv_double_quotes_values():
    result = export({"X": "hello"}, "dotenv")
    assert result.strip() == 'X="hello"'


def test_dotenv_escapes_double_quotes_in_value():
    result = export({"MSG": 'say "hi"'}, "dotenv")
    assert '\\"' in result


def test_dotenv_ends_with_newline():
    result = export({"A": "1"}, "dotenv")
    assert result.endswith("\n")


def test_dotenv_empty_secrets():
    assert export({}, "dotenv") == ""


# ---------------------------------------------------------------------------
# shell format
# ---------------------------------------------------------------------------

def test_shell_uses_export_keyword():
    result = export({"FOO": "bar"}, "shell")
    assert result.startswith("export FOO=")


def test_shell_single_quotes_value():
    result = export({"X": "hello world"}, "shell")
    assert "'hello world'" in result


def test_shell_escapes_single_quote_in_value():
    result = export({"X": "it's"}, "shell")
    # The single-quote escape sequence must be present
    assert "'\"'\"'" in result


def test_shell_ends_with_newline():
    result = export({"A": "1"}, "shell")
    assert result.endswith("\n")


# ---------------------------------------------------------------------------
# json format
# ---------------------------------------------------------------------------

def test_json_is_valid_json():
    result = export(SAMPLE, "json")
    parsed = json.loads(result)
    assert parsed == SAMPLE


def test_json_sorted_keys():
    result = export({"Z": "1", "A": "2"}, "json")
    parsed = json.loads(result)
    assert list(parsed.keys()) == sorted(parsed.keys())


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------

def test_unsupported_format_raises():
    with pytest.raises(ExportError, match="Unsupported format"):
        export({"K": "v"}, "xml")


def test_supported_formats_constant():
    assert "dotenv" in SUPPORTED_FORMATS
    assert "shell" in SUPPORTED_FORMATS
    assert "json" in SUPPORTED_FORMATS
