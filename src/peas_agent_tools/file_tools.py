"""File read/write/list LangChain tools."""

from __future__ import annotations

from langchain_core.tools import tool

from peas_agent_tools.paths import resolve_project_path, resolve_readable_path


@tool("read_file")
def read_file(path: str, offset: int = 1, limit: int = 200) -> str:
    """讀取 UTF-8 文字檔，回傳帶行號內容。接受絕對路徑或相對於 project root 的路徑。"""
    try:
        target = resolve_readable_path(path)
        if not target.is_file():
            return f"Error: not a file: {path}"
        lines = target.read_text(encoding="utf-8").splitlines()
        start = max(offset - 1, 0)
        end = min(start + limit, len(lines))
        return "\n".join(f"{i + 1}| {line}" for i, line in enumerate(lines[start:end], start))
    except Exception as e:
        return f"Error: {e}"


@tool("write_file")
def write_file(path: str, content: str) -> str:
    """整檔覆寫寫入 UTF-8 文字檔（必要時建立父資料夾）。接受絕對路徑或相對於 project root 的路徑。"""
    try:
        target = resolve_project_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error: {e}"


@tool("edit_file")
def edit_file(path: str, old_text: str, new_text: str, replace_all: bool = False) -> str:
    """在既有檔案中把 old_text 換成 new_text（預設僅單次替換）。接受絕對路徑或相對於 project root 的路徑。"""
    try:
        target = resolve_project_path(path)
        text = target.read_text(encoding="utf-8")
        count = text.count(old_text)
        if count == 0:
            return "Error: old_text not found"
        if count > 1 and not replace_all:
            return "Error: old_text appears multiple times"
        target.write_text(
            text.replace(old_text, new_text, -1 if replace_all else 1),
            encoding="utf-8",
        )
        return f"edited {path}"
    except Exception as e:
        return f"Error: {e}"


@tool("list_dir")
def list_dir(path: str, recursive: bool = False, max_entries: int = 200) -> str:
    """列出資料夾內容。接受絕對路徑或相對於 project root 的路徑。"""
    try:
        root = resolve_project_path(path)
        if not root.is_dir():
            return f"Error: not a directory: {path}"
        iterator = root.rglob("*") if recursive else root.iterdir()
        entries = [str(item) for item in iterator][:max_entries]
        return "\n".join(entries) if entries else "(empty)"
    except Exception as e:
        return f"Error: {e}"
