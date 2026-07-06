"""Unified tools config: peas-tools.json, configure_tools, auto-load."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from peas_agent_tools.config import ToolSettings, configure, get_settings
from peas_agent_tools.vcr_image import configure_image
from peas_agent_tools.web import configure_web

TOOLS_CONFIG_FILENAME = "peas-tools.json"

DEFAULT_TOOLS_CONFIG: dict[str, Any] = {
    "tools": {
        "web": {
            "enable": True,
            "search": {
                "provider": "duckduckgo",
                "apiKey": "",
                "maxResults": 5,
                "timeout": 30,
            },
            "fetch": {
                "useJinaReader": True,
                "maxChars": 50000,
            },
        },
        "image": {
            "enable": True,
            "apiKey": "",
            "baseUrl": "https://ai.vanscoding.com/v1",
            "timeout": 120,
        },
        "exec": {
            "execDefaultTimeout": 120,
        },
    }
}

_CONFIG_APPLIED = False
_EXPLICIT_CONFIGURE = False


def _str(d: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        val = d.get(key)
        if isinstance(val, str):
            return val
    return default


def _int(d: dict[str, Any], *keys: str, default: int) -> int:
    for key in keys:
        val = d.get(key)
        try:
            return int(val)
        except (TypeError, ValueError):
            continue
    return default


def deep_merge_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Shallow-merge top-level keys; recurse into nested dicts without overwriting leaves."""
    out = deepcopy(base)
    for key, value in patch.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = deep_merge_dict(out[key], value)
        elif key not in out:
            out[key] = deepcopy(value)
    return out


def configure_tools(config: dict[str, Any]) -> None:
    """Apply tools.* settings from peas-tools.json (or explicit dict)."""
    global _CONFIG_APPLIED, _EXPLICIT_CONFIGURE
    configure_web(config)
    configure_image(config)

    tools = config.get("tools") if isinstance(config.get("tools"), dict) else {}
    exec_cfg = tools.get("exec") if isinstance(tools.get("exec"), dict) else {}
    timeout = _int(exec_cfg, "execDefaultTimeout", "exec_default_timeout", default=0)
    if timeout > 0:
        current = get_settings()
        configure(
            ToolSettings(
                project_root=current.project_root,
                workspace=current.workspace,
                package_dir=current.package_dir,
                exec_default_timeout=timeout,
            )
        )

    _EXPLICIT_CONFIGURE = True
    _CONFIG_APPLIED = True


def reset_tools_config_for_tests() -> None:
    """Reset auto-load state (tests only)."""
    global _CONFIG_APPLIED, _EXPLICIT_CONFIGURE
    _CONFIG_APPLIED = False
    _EXPLICIT_CONFIGURE = False
    configure_web({"tools": {"web": {"enable": True}}})
    configure_image({"tools": {"image": {"enable": True, "apiKey": ""}}})


def _tools_config_path() -> Path:
    return get_settings().project_root / TOOLS_CONFIG_FILENAME


def _ensure_tools_config() -> None:
    global _CONFIG_APPLIED
    if _CONFIG_APPLIED:
        return
    if os.environ.get("PEAS_AGENT_NO_AUTO_CONFIG", "").strip() in {"1", "true", "yes"}:
        _CONFIG_APPLIED = True
        return

    path = _tools_config_path()
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            loaded = {}
        if isinstance(loaded, dict):
            configure_tools(loaded)
            return

    _CONFIG_APPLIED = True


def default_tools_config() -> dict[str, Any]:
    return deepcopy(DEFAULT_TOOLS_CONFIG)
