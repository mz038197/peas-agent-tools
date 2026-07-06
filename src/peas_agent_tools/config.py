"""Runtime tool settings (project root, workspace fallbacks, exec timeout)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT_MARKERS = (".git", "pyproject.toml", "uv.lock")


@dataclass(frozen=True)
class ToolSettings:
    project_root: Path
    workspace: Path | None = None
    package_dir: Path | None = None
    exec_default_timeout: int = 120


_EXPLICIT_SETTINGS: ToolSettings | None = None


def discover_project_root(start: Path | None = None) -> Path:
    """Walk up from start (default cwd) for repo markers; return start dir if none found."""
    current = (start or Path.cwd()).expanduser().resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if any((candidate / marker).exists() for marker in PROJECT_ROOT_MARKERS):
            return candidate
    return current


def _resolve_default_project_root() -> Path:
    env_project = os.environ.get("PEAS_AGENT_PROJECT_ROOT")
    if env_project:
        return Path(env_project).expanduser().resolve()
    return discover_project_root(Path.cwd())


def _resolve_default_settings() -> ToolSettings:
    return ToolSettings(project_root=_resolve_default_project_root())


def configure(settings: ToolSettings) -> None:
    global _EXPLICIT_SETTINGS
    _EXPLICIT_SETTINGS = ToolSettings(
        project_root=settings.project_root.expanduser().resolve(),
        workspace=(
            settings.workspace.expanduser().resolve()
            if settings.workspace is not None
            else None
        ),
        package_dir=(
            settings.package_dir.expanduser().resolve()
            if settings.package_dir is not None
            else None
        ),
        exec_default_timeout=(
            settings.exec_default_timeout
            if settings.exec_default_timeout > 0
            else 120
        ),
    )


def get_settings() -> ToolSettings:
    if _EXPLICIT_SETTINGS is not None:
        return _EXPLICIT_SETTINGS
    return _resolve_default_settings()


def get_exec_default_timeout() -> int:
    return get_settings().exec_default_timeout
