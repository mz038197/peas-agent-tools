from __future__ import annotations

from pathlib import Path

from peas_agent_tools import ToolSettings, configure
from peas_agent_tools.image_tools import create_read_image_tool


def test_read_image_missing_file(tmp_path: Path) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    read_image = create_read_image_tool(lambda *_args: "analysis")
    out = read_image.invoke({"path": "missing.png"})
    assert out.startswith("Error: not a file:")


def test_read_image_unsupported_extension(tmp_path: Path) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    gif = tmp_path / "x.gif"
    gif.write_bytes(b"GIF89a")
    read_image = create_read_image_tool(lambda *_args: "analysis")
    out = read_image.invoke({"path": "x.gif"})
    assert "unsupported image type" in out


def test_read_image_too_large(tmp_path: Path) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    png = tmp_path / "big.png"
    png.write_bytes(b"\x00" * (8 * 1024 * 1024 + 1))
    read_image = create_read_image_tool(lambda *_args: "analysis")
    out = read_image.invoke({"path": "big.png"})
    assert "image too large" in out


def test_read_image_success(tmp_path: Path) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n")

    def analyzer(path: str, question: str, data: bytes, media_type: str) -> str:
        assert path == "screen.png"
        assert question == "filter 是否為 BMW？"
        assert data.startswith(b"\x89PNG")
        assert media_type == "image/png"
        return "filter chip 顯示 BMW"

    read_image = create_read_image_tool(analyzer)
    out = read_image.invoke({"path": "screen.png", "question": "filter 是否為 BMW？"})
    assert "[read_image: screen.png]" in out
    assert "Question: filter 是否為 BMW？" in out
    assert "Analysis:" in out
    assert "BMW" in out


def test_read_image_empty_vision_response(tmp_path: Path) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n")
    read_image = create_read_image_tool(lambda *_args: "   ")
    out = read_image.invoke({"path": "screen.png"})
    assert "empty response" in out
