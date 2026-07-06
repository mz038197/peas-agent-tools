"""Runtime tool settings (project root, workspace fallbacks, exec timeout)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_DEFAULT_PROJECT_ROOT = Path.cwd().resolve()


@dataclass(frozen=True)
class ToolSettings:
    project_root: Path
    workspace: Path | None = None
    package_dir: Path | None = None
    exec_default_timeout: int = 120


_SETTINGS: ToolSettings = ToolSettings(project_root=_DEFAULT_PROJECT_ROOT)


def configure(settings: ToolSettings) -> None:
    global _SETTINGS
    _SETTINGS = ToolSettings(
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
    return _SETTINGS


def get_exec_default_timeout() -> int:
    return get_settings().exec_default_timeout
