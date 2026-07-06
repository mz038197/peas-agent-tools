"""Vision read_image tool factory."""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.tools import StructuredTool

from peas_agent_tools.media import guess_media_type
from peas_agent_tools.paths import resolve_project_image_path

_READ_IMAGE_ALLOWED_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp"})
_READ_IMAGE_MAX_BYTES = 8 * 1024 * 1024

VisionAnalyzer = Callable[[str, str, bytes, str], str]


def create_read_image_tool(analyzer: VisionAnalyzer) -> StructuredTool:
    """Build read_image tool bound to the given vision analyzer callback."""

    def _read_image(path: str, question: str = "描述此截圖內容。") -> str:
        """分析專案內 PNG/JPEG/WebP 截圖（nested vision），回傳文字描述供自我驗證。"""
        try:
            target = resolve_project_image_path(path)
            if not target.is_file():
                return f"Error: not a file: {path}"
            suffix = target.suffix.lower()
            if suffix not in _READ_IMAGE_ALLOWED_SUFFIXES:
                allowed = ", ".join(sorted(_READ_IMAGE_ALLOWED_SUFFIXES))
                return (
                    f"Error: unsupported image type: {suffix or '(no extension)'} "
                    f"(use {allowed})"
                )
            size = target.stat().st_size
            if size > _READ_IMAGE_MAX_BYTES:
                return f"Error: image too large ({size} bytes; max {_READ_IMAGE_MAX_BYTES})"
            media_type = guess_media_type(target)
            data = target.read_bytes()
            analysis = analyzer(path, question, data, media_type)
            if not (analysis or "").strip():
                return f"Error: vision model returned empty response for {path}"
            q = (question or "").strip() or "描述此截圖內容。"
            return f"[read_image: {path}]\nQuestion: {q}\nAnalysis:\n{analysis}"
        except RuntimeError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error: {e}"

    return StructuredTool.from_function(
        func=_read_image,
        name="read_image",
        description="分析專案內 PNG/JPEG/WebP 截圖（nested vision），回傳文字描述供自我驗證。",
    )


def read_image_without_analyzer(path: str, question: str = "描述此截圖內容。") -> str:
    """Placeholder when no vision analyzer is configured."""
    _ = path, question
    return "Error: read_image requires a vision_analyzer; configure via get_builtin_tools()"
