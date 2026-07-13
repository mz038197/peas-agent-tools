from __future__ import annotations

import json
from pathlib import Path

import pytest

from peas_agent_tools import ToolSettings, configure, get_builtin_tools
from peas_agent_tools.tools_config import (
    TOOLS_CONFIG_FILENAME,
    configure_tools,
    reset_tools_config_for_tests,
)
from peas_agent_tools.vcr_image import configure_image, image_tools_enabled
from peas_agent_tools.web import configure_web, web_tools_enabled


@pytest.fixture(autouse=True)
def reset_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VCR_API_KEY", raising=False)
    monkeypatch.setenv("PEAS_AGENT_NO_AUTO_CONFIG", "1")
    reset_tools_config_for_tests()
    yield
    reset_tools_config_for_tests()


def test_configure_image_api_key() -> None:
    configure_image({"tools": {"image": {"enable": True, "apiKey": "vcr_sk_x"}}})
    assert image_tools_enabled()


def test_configure_image_disabled() -> None:
    configure_image({"tools": {"image": {"enable": False, "apiKey": "vcr_sk_x"}}})
    assert not image_tools_enabled()


def test_configure_image_no_key() -> None:
    configure_image({"tools": {"image": {"enable": True, "apiKey": ""}}})
    assert not image_tools_enabled()


def test_configure_tools_exec_timeout(tmp_path: Path) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    configure_tools({"tools": {"exec": {"execDefaultTimeout": 99}}})
    from peas_agent_tools import get_exec_default_timeout

    assert get_exec_default_timeout() == 99


def test_configure_tools_web_fetch(tmp_path: Path) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    configure_tools(
        {
            "tools": {
                "web": {
                    "fetch": {"useJinaReader": False, "maxChars": 1000},
                }
            }
        }
    )
    from peas_agent_tools.web import _WEB_SETTINGS

    assert _WEB_SETTINGS.fetch.use_jina_reader is False
    assert _WEB_SETTINGS.fetch.max_chars == 1000


def test_auto_load_peas_tools_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    config = {
        "tools": {
            "image": {"enable": True, "apiKey": "vcr_sk_auto"},
            "web": {"enable": False},
        }
    }
    (tmp_path / TOOLS_CONFIG_FILENAME).write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.delenv("VCR_API_KEY", raising=False)
    monkeypatch.delenv("PEAS_AGENT_NO_AUTO_CONFIG", raising=False)
    reset_tools_config_for_tests()

    names = {t.name for t in get_builtin_tools()}
    assert "generate_image" in names
    assert "web_search" not in names
    assert image_tools_enabled()
    assert not web_tools_enabled()


def test_auto_load_skipped_when_no_auto_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    (tmp_path / TOOLS_CONFIG_FILENAME).write_text(
        json.dumps({"tools": {"web": {"enable": False}}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("PEAS_AGENT_NO_AUTO_CONFIG", "1")

    names = {t.name for t in get_builtin_tools()}
    assert "web_search" in names
