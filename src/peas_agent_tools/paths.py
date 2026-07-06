"""Filesystem path resolution for built-in tools."""

from __future__ import annotations

from pathlib import Path

from peas_agent_tools.config import get_settings


def resolve_project_path(path: str) -> Path:
    """Absolute paths are used as-is; relative paths are under project_root."""
    raw = Path(path)
    if raw.is_absolute():
        return raw.expanduser().resolve()
    return (get_settings().project_root / path).expanduser().resolve()


def resolve_workspace_path(path: str) -> Path:
    """Deprecated alias; resolves relative paths against project_root."""
    return resolve_project_path(path)


def resolve_readable_path(path: str) -> Path:
    """Resolve a readable file path, with workspace/package fallbacks."""
    target = resolve_project_path(path)
    if target.is_file():
        return target

    if not Path(path).is_absolute():
        settings = get_settings()
        if settings.workspace is not None:
            workspace_target = (settings.workspace / path).expanduser().resolve()
            if workspace_target.is_file():
                return workspace_target
        if settings.package_dir is not None:
            pkg_target = (settings.package_dir / path).expanduser().resolve()
            if pkg_target.is_file():
                return pkg_target
    return target


def resolve_project_image_path(rel: str) -> Path:
    """Resolve image path; relative paths are under project_root."""
    raw = Path(rel)
    if raw.is_absolute():
        return raw.expanduser().resolve()
    return (get_settings().project_root / rel).expanduser().resolve()
