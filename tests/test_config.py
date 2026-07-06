from __future__ import annotations

from pathlib import Path

import pytest

from peas_agent_tools import ToolSettings, configure, discover_project_root, get_settings


@pytest.fixture(autouse=True)
def reset_configure() -> None:
    import peas_agent_tools.config as config_mod

    config_mod._EXPLICIT_SETTINGS = None
    yield
    config_mod._EXPLICIT_SETTINGS = None


def test_discover_project_root_finds_pyproject_parent(tmp_path: Path) -> None:
    project = tmp_path / "project"
    nested = project / "src" / "feature"
    nested.mkdir(parents=True)
    (project / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    assert discover_project_root(nested) == project.resolve()


def test_discover_project_root_fallback_to_start(tmp_path: Path) -> None:
    start = tmp_path / "plain"
    start.mkdir()
    assert discover_project_root(start) == start.resolve()


def test_get_settings_without_configure_uses_discover(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    nested = project / "sub"
    nested.mkdir(parents=True)
    (project / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    monkeypatch.chdir(nested)

    assert get_settings().project_root == project.resolve()


def test_peas_agent_project_root_env_overrides_discover(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "from-env"
    project.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.setenv("PEAS_AGENT_PROJECT_ROOT", str(project))
    monkeypatch.chdir(other)

    assert get_settings().project_root == project.resolve()


def test_configure_overrides_auto_discover(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    explicit = tmp_path / "explicit"
    explicit.mkdir()
    monkeypatch.chdir(tmp_path)

    configure(ToolSettings(project_root=explicit))
    assert get_settings().project_root == explicit.resolve()
