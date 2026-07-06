from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from peas_agent_tools import ToolSettings, configure
from peas_agent_tools.exec_tools import exec_workspace
from peas_agent_tools.file_tools import write_file
from peas_agent_tools.paths import resolve_project_image_path, resolve_project_path


def test_relative_file_paths_resolve_to_project_root(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    configure(ToolSettings(project_root=project.resolve()))

    write_file.invoke({"path": "src/app.py", "content": "print('project')\n"})

    assert (project / "src" / "app.py").read_text(encoding="utf-8") == "print('project')\n"


def test_resolve_project_path_keeps_absolute_paths(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.txt"
    configure(ToolSettings(project_root=project.resolve()))

    assert resolve_project_path(str(outside)) == outside.resolve()


def test_image_relative_paths_resolve_to_project_root(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    image = project / "screen.png"
    image.write_bytes(b"not-real-png")
    configure(ToolSettings(project_root=project.resolve()))

    assert resolve_project_image_path("screen.png") == image.resolve()


def test_exec_defaults_to_project_root(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    configure(ToolSettings(project_root=project.resolve()))

    with patch("peas_agent_tools.exec_tools.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"ok"
        mock_run.return_value.stderr = b""
        exec_workspace.invoke({"command": "echo hi"})

    assert mock_run.call_args.kwargs["cwd"] == str(project.resolve())


def test_exec_default_timeout_from_config(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    configure(ToolSettings(project_root=project.resolve(), exec_default_timeout=120))

    with patch("peas_agent_tools.exec_tools.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"ok"
        mock_run.return_value.stderr = b""
        exec_workspace.invoke({"command": "echo hi"})

    assert mock_run.call_args.kwargs["timeout"] == 120


def test_exec_explicit_timeout_overrides_config(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    configure(ToolSettings(project_root=project.resolve(), exec_default_timeout=120))

    with patch("peas_agent_tools.exec_tools.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"ok"
        mock_run.return_value.stderr = b""
        exec_workspace.invoke({"command": "echo hi", "timeout": 45})

    assert mock_run.call_args.kwargs["timeout"] == 45
