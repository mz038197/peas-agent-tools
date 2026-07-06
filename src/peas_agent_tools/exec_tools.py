"""Shell exec LangChain tool."""

from __future__ import annotations

import locale
import os
import subprocess
from typing import Any

from langchain_core.tools import tool

from peas_agent_tools.config import get_exec_default_timeout, get_settings
from peas_agent_tools.paths import resolve_project_path


def decode_process_output(data: bytes) -> str:
    encodings = ["utf-8", locale.getpreferredencoding(False), "cp950"]
    for encoding in dict.fromkeys(encodings):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


@tool("exec")
def exec_workspace(command: str, timeout: int | None = None, cwd: str | None = None) -> str:
    """執行 shell 指令（已阻擋常見危險片段）。可選 cwd 指定工作目錄；預設為 project root。"""
    if timeout is None:
        timeout = get_exec_default_timeout()
    blocked = ("rm -rf", "del /f", "rmdir /s", "format", "shutdown")
    lowered = command.lower()
    if any(part in lowered for part in blocked):
        return "Error: blocked dangerous command (safety limit)"
    if os.name == "nt" and "<<" in command:
        return (
            "Error: heredoc syntax is disabled in this Windows runtime. "
            "Use write_file to create a .py script, then run it with "
            "uv run python <script.py>."
        )

    project_root = get_settings().project_root
    work_dir = resolve_project_path(cwd) if cwd else project_root
    if not work_dir.is_dir():
        return f"Error: not a directory: {cwd or project_root}"

    child_env = os.environ.copy()
    child_env.setdefault("PYTHONUTF8", "1")
    child_env.setdefault("PYTHONIOENCODING", "utf-8")

    run_kw: dict[str, Any] = {
        "cwd": str(work_dir),
        "shell": True,
        "capture_output": True,
        "timeout": timeout,
        "env": child_env,
    }
    if os.name == "nt":
        run_kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    try:
        result = subprocess.run(command, **run_kw)
        stdout = decode_process_output(result.stdout or b"")
        stderr = decode_process_output(result.stderr or b"")
        output = (stdout + stderr).strip()
        cap = 4000
        if len(output) > cap:
            output = output[:cap] + "\n\n[truncated]"
        if not output:
            output = "(no stdout or stderr; command finished with no captured output)"
        return f"exit_code={result.returncode}\n{output}"
    except Exception as e:
        return f"Error: {e}"
