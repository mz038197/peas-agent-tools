"""Built-in tool registry and presets."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from peas_agent_tools.demo import add_numbers
from peas_agent_tools.exec_tools import exec_workspace
from peas_agent_tools.file_tools import edit_file, list_dir, read_file, write_file
from peas_agent_tools.image_tools import VisionAnalyzer, create_read_image_tool, generate_image
from peas_agent_tools.tools_config import _ensure_tools_config
from peas_agent_tools.vcr_image import image_tools_enabled
from peas_agent_tools.web import web_fetch, web_search, web_tools_enabled

BUILTIN_TOOL_NAMES: tuple[str, ...] = (
    "add_numbers",
    "read_file",
    "read_image",
    "generate_image",
    "write_file",
    "edit_file",
    "list_dir",
    "exec",
    "web_search",
    "web_fetch",
)

_DEFAULT_TOOL_ORDER: tuple[str, ...] = (
    "add_numbers",
    "read_file",
    "read_image",
    "generate_image",
    "write_file",
    "edit_file",
    "list_dir",
    "exec",
    "web_search",
    "web_fetch",
)


def get_file_tools() -> list[Any]:
    return [read_file, write_file, edit_file, list_dir]


def get_exec_tool() -> Any:
    return exec_workspace


def get_web_tools() -> list[Any]:
    return [web_search, web_fetch]


def _read_image_tool(vision_analyzer: VisionAnalyzer | None) -> Any:
    if vision_analyzer is not None:
        return create_read_image_tool(vision_analyzer)
    return create_read_image_tool(
        lambda _path, _q, _data, _mt: (
            "Error: read_image requires vision_analyzer in get_builtin_tools()"
        )
    )


def _build_tool_map(*, vision_analyzer: VisionAnalyzer | None = None) -> dict[str, Any]:
    return {
        "add_numbers": add_numbers,
        "read_file": read_file,
        "read_image": _read_image_tool(vision_analyzer),
        "generate_image": generate_image,
        "write_file": write_file,
        "edit_file": edit_file,
        "list_dir": list_dir,
        "exec": exec_workspace,
        "web_search": web_search,
        "web_fetch": web_fetch,
    }


def get_builtin_tools(
    *,
    include: Sequence[str] | None = None,
    vision_analyzer: VisionAnalyzer | None = None,
) -> list[Any]:
    _ensure_tools_config()
    tool_map = _build_tool_map(vision_analyzer=vision_analyzer)

    if include is None:
        names = list(_DEFAULT_TOOL_ORDER)
        if not web_tools_enabled():
            names = [name for name in names if name not in {"web_search", "web_fetch"}]
        if not image_tools_enabled():
            names = [name for name in names if name != "generate_image"]
        return [tool_map[name] for name in names]

    if not include:
        return []

    tools: list[Any] = []
    for name in include:
        if name not in tool_map:
            valid = ", ".join(BUILTIN_TOOL_NAMES)
            raise ValueError(f"Unknown builtin tool {name!r}. Valid names: {valid}")
        tools.append(tool_map[name])
    return tools
