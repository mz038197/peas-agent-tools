"""Scaffold peas-tools.json in student projects."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from peas_agent_tools.config import discover_project_root
from peas_agent_tools.tools_config import (
    DEFAULT_TOOLS_CONFIG,
    TOOLS_CONFIG_FILENAME,
    deep_merge_dict,
)

_GENERATED_DIR = "assets/generated"


def run_init(*, cwd: Path, merge: bool) -> list[str]:
    messages: list[str] = []
    config_path = cwd / TOOLS_CONFIG_FILENAME

    if config_path.is_file():
        if merge:
            try:
                existing = json.loads(config_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = {}
            if not isinstance(existing, dict):
                existing = {}
            merged = deep_merge_dict(existing, DEFAULT_TOOLS_CONFIG)
            config_path.write_text(
                json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            messages.append(f"merged {TOOLS_CONFIG_FILENAME}")
        else:
            messages.append(f"skipped {TOOLS_CONFIG_FILENAME} (already exists; use --merge)")
    else:
        config_path.write_text(
            json.dumps(DEFAULT_TOOLS_CONFIG, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        messages.append(f"created {TOOLS_CONFIG_FILENAME}")

    generated = cwd / _GENERATED_DIR
    generated.mkdir(parents=True, exist_ok=True)
    messages.append(f"ensured {_GENERATED_DIR}/")
    return messages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create peas-tools.json scaffold for peas-agent-tools"
    )
    parser.add_argument("--cwd", default="", help="Project root (default: auto-discover)")
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge missing tools.* keys into existing peas-tools.json",
    )
    args = parser.parse_args(argv)

    cwd = Path(args.cwd).resolve() if args.cwd else discover_project_root()
    messages = run_init(cwd=cwd, merge=args.merge)
    for line in messages:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
