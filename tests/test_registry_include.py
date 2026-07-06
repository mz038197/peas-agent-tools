from __future__ import annotations

import pytest

from peas_agent_tools import BUILTIN_TOOL_NAMES, get_builtin_tools
from peas_agent_tools.web import configure_web


@pytest.fixture(autouse=True)
def reset_web_settings() -> None:
    configure_web({"tools": {"web": {"enable": True}}})
    yield
    configure_web({"tools": {"web": {"enable": True}}})


def test_include_none_matches_full_default_set() -> None:
    tools = get_builtin_tools()
    names = {t.name for t in tools}
    assert names == {
        "add_numbers",
        "read_file",
        "read_image",
        "write_file",
        "edit_file",
        "list_dir",
        "exec",
        "web_search",
        "web_fetch",
    }


def test_include_subset() -> None:
    tools = get_builtin_tools(include=["read_file", "list_dir"])
    assert [t.name for t in tools] == ["read_file", "list_dir"]


def test_include_empty_list() -> None:
    assert get_builtin_tools(include=[]) == []


def test_include_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown builtin tool 'nope'"):
        get_builtin_tools(include=["nope"])


def test_include_web_search_when_web_disabled() -> None:
    configure_web({"tools": {"web": {"enable": False}}})
    tools = get_builtin_tools(include=["web_search"])
    assert [t.name for t in tools] == ["web_search"]


def test_include_none_omits_web_when_disabled() -> None:
    configure_web({"tools": {"web": {"enable": False}}})
    names = {t.name for t in get_builtin_tools()}
    assert "web_search" not in names
    assert "web_fetch" not in names


def test_builtin_tool_names_constant() -> None:
    assert len(BUILTIN_TOOL_NAMES) == 9
