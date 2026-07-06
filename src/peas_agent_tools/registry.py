"""Built-in tool registry and presets."""

from __future__ import annotations

from typing import Any

from peas_agent_tools.demo import add_numbers
from peas_agent_tools.exec_tools import exec_workspace
from peas_agent_tools.file_tools import edit_file, list_dir, read_file, write_file
from peas_agent_tools.image_tools import VisionAnalyzer, create_read_image_tool
from peas_agent_tools.web import web_fetch, web_search, web_tools_enabled


def get_file_tools() -> list[Any]:
    return [read_file, write_file, edit_file, list_dir]


def get_exec_tool() -> Any:
    return exec_workspace


def get_web_tools() -> list[Any]:
    return [web_search, web_fetch]


def get_builtin_tools(*, vision_analyzer: VisionAnalyzer | None = None) -> list[Any]:
    if vision_analyzer is not None:
        read_image = create_read_image_tool(vision_analyzer)
    else:
        read_image = create_read_image_tool(
            lambda _path, _q, _data, _mt: (
                "Error: read_image requires vision_analyzer in get_builtin_tools()"
            )
        )
    tools: list[Any] = [
        add_numbers,
        read_file,
        read_image,
        write_file,
        edit_file,
        list_dir,
        exec_workspace,
    ]
    if web_tools_enabled():
        tools.extend(get_web_tools())
    return tools
