from __future__ import annotations

import json
from pathlib import Path

import pytest

from peas_agent_tools.init_cli import run_init
from peas_agent_tools.tools_config import TOOLS_CONFIG_FILENAME, deep_merge_dict


def test_run_init_creates_peas_tools_json(tmp_path: Path) -> None:
    messages = run_init(cwd=tmp_path, merge=False)
    config_path = tmp_path / TOOLS_CONFIG_FILENAME
    assert config_path.is_file()
    assert (tmp_path / "assets" / "generated").is_dir()
    assert any("created" in m for m in messages)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert "tools" in data
    assert "web" in data["tools"]
    assert "image" in data["tools"]
    assert "exec" in data["tools"]
    assert not (tmp_path / ".vans").exists()


def test_run_init_skips_existing(tmp_path: Path) -> None:
    config_path = tmp_path / TOOLS_CONFIG_FILENAME
    config_path.write_text('{"tools": {"web": {"enable": false}}}', encoding="utf-8")
    messages = run_init(cwd=tmp_path, merge=False)
    assert json.loads(config_path.read_text())["tools"]["web"]["enable"] is False
    assert any("skipped" in m for m in messages)


def test_run_init_merge_adds_image(tmp_path: Path) -> None:
    config_path = tmp_path / TOOLS_CONFIG_FILENAME
    config_path.write_text(
        json.dumps({"tools": {"web": {"enable": True, "search": {"provider": "brave"}}}}),
        encoding="utf-8",
    )
    run_init(cwd=tmp_path, merge=True)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data["tools"]["web"]["search"]["provider"] == "brave"
    assert "image" in data["tools"]
    assert "exec" in data["tools"]


def test_deep_merge_preserves_existing() -> None:
    base = {"tools": {"web": {"search": {"provider": "brave", "apiKey": "secret"}}}}
    patch = {"tools": {"image": {"apiKey": ""}, "web": {"search": {"maxResults": 5}}}}
    merged = deep_merge_dict(base, patch)
    assert merged["tools"]["web"]["search"]["provider"] == "brave"
    assert merged["tools"]["web"]["search"]["apiKey"] == "secret"
    assert merged["tools"]["image"]["apiKey"] == ""
