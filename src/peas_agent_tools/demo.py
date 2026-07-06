"""Workshop demo tool."""

from __future__ import annotations

from langchain_core.tools import tool


@tool
def add_numbers(a: float, b: float) -> float:
    """兩個數字相加並回傳和。純算術必須呼叫此工具，不可心算後直接回答。"""
    return float(a) + float(b)
