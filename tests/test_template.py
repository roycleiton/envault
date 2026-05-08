"""Tests for envault.template."""
from __future__ import annotations

import pytest

from envault.template import TemplateError, render_file, render_string
from envault.vault import Vault


@pytest.fixture()
def vault(tmp_path):
    v = Vault(tmp_path / "vault.enc")
    v.set("DB_HOST", "localhost", "secret")
    v.set("DB_PORT", "5432", "secret")
    v.set("API_KEY", "abc123", "secret")
    return v


def test_render_single_placeholder(vault):
    result = render_string("host={{ DB_HOST }}", vault, "secret")
    assert result == "host=localhost"


def test_render_multiple_placeholders(vault):
    result = render_string("{{ DB_HOST }}:{{ DB_PORT }}", vault, "secret")
    assert result == "localhost:5432"


def test_render_placeholder_with_extra_whitespace(vault):
    result = render_string("key={{  API_KEY  }}", vault, "secret")
    assert result == "key=abc123"


def test_render_no_placeholders(vault):
    result = render_string("no placeholders here", vault, "secret")
    assert result == "no placeholders here"


def test_render_strict_raises_on_missing_key(vault):
    with pytest.raises(TemplateError, match="MISSING_KEY"):
        render_string("value={{ MISSING_KEY }}", vault, "secret", strict=True)


def test_render_non_strict_leaves_unknown_placeholder(vault):
    result = render_string("value={{ MISSING_KEY }}", vault, "secret", strict=False)
    assert "{{ MISSING_KEY }}" in result


def test_render_wrong_passphrase_raises(vault):
    with pytest.raises(Exception):
        render_string("{{ DB_HOST }}", vault, "wrong-passphrase", strict=True)


def test_render_file_basic(vault, tmp_path):
    src = tmp_path / "config.tmpl"
    src.write_text("DATABASE_URL=postgres://{{ DB_HOST }}:{{ DB_PORT }}/mydb")
    result = render_file(src, vault, "secret")
    assert result == "DATABASE_URL=postgres://localhost:5432/mydb"


def test_render_file_writes_dst(vault, tmp_path):
    src = tmp_path / "config.tmpl"
    dst = tmp_path / "out" / "config.env"
    src.write_text("API={{ API_KEY }}")
    render_file(src, vault, "secret", dst)
    assert dst.exists()
    assert dst.read_text() == "API=abc123"


def test_render_file_missing_src_raises(vault, tmp_path):
    with pytest.raises(TemplateError, match="not found"):
        render_file(tmp_path / "nonexistent.tmpl", vault, "secret")


def test_render_file_returns_rendered_string_without_dst(vault, tmp_path):
    src = tmp_path / "t.tmpl"
    src.write_text("{{ DB_HOST }}")
    result = render_file(src, vault, "secret")
    assert result == "localhost"
