from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from peas_agent_tools import ToolSettings, configure, generate_image
from peas_agent_tools.tools_config import reset_tools_config_for_tests
from peas_agent_tools.vcr_image import configure_image, generate_vcr_image


@pytest.fixture(autouse=True)
def reset_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VCR_API_KEY", raising=False)
    monkeypatch.setenv("PEAS_AGENT_NO_AUTO_CONFIG", "1")
    reset_tools_config_for_tests()
    yield
    reset_tools_config_for_tests()


def test_generate_image_missing_api_key(tmp_path: Path) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    configure_image({"tools": {"image": {"enable": True, "apiKey": ""}}})
    out = generate_image.invoke({"prompt": "a pea icon"})
    assert "Missing API key" in out


def test_generate_image_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    configure_image({"tools": {"image": {"enable": True, "apiKey": "vcr_sk_test"}}})

    fake_png = b"\x89PNG\r\n\x1a\n"
    b64 = __import__("base64").b64encode(fake_png).decode("ascii")

    with patch("peas_agent_tools.vcr_image.httpx.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": [{"b64_json": b64}],
            "usage": {"total_tokens": 42},
        }
        mock_post.return_value = mock_response

        out = generate_image.invoke(
            {"prompt": "flat pea icon", "preset": "icon", "output_path": "assets/generated/x.png"}
        )

    payload = json.loads(out)
    assert payload["path"] == "assets/generated/x.png"
    assert "flux.2-klein-4b" in payload["model"]
    written = tmp_path / "assets" / "generated" / "x.png"
    assert written.read_bytes() == fake_png


def test_preset_icon_model(tmp_path: Path) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    configure_image({"tools": {"image": {"apiKey": "k"}}})
    captured: dict = {}

    with patch("peas_agent_tools.vcr_image._post_images") as mock_post:
        mock_post.return_value = {"data": [{"b64_json": ""}], "usage": {}}
        with patch("peas_agent_tools.vcr_image._extract_b64", return_value=b"x"):
            generate_vcr_image(prompt="hi", preset="icon", output_path="out.png")
        captured = mock_post.call_args[0][2]

    assert captured["model"] == "openrouter@black-forest-labs/flux.2-klein-4b"


def test_reference_uses_edit_model(tmp_path: Path) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    configure_image({"tools": {"image": {"apiKey": "k"}}})
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"\x89PNG\r\n")
    captured: dict = {}

    with patch("peas_agent_tools.vcr_image._post_images") as mock_post:
        mock_post.return_value = {"data": [{"b64_json": ""}], "usage": {}}
        with patch("peas_agent_tools.vcr_image._extract_b64", return_value=b"x"):
            generate_vcr_image(
                prompt="edit",
                output_path="out.png",
                reference_paths=["ref.png"],
            )
        captured = mock_post.call_args[0][2]

    assert captured["model"] == "openrouter@openai/gpt-5.4-image-2"
    assert "input_references" in captured


def test_output_outside_project_root(tmp_path: Path) -> None:
    configure(ToolSettings(project_root=tmp_path.resolve()))
    configure_image({"tools": {"image": {"apiKey": "k"}}})
    out = generate_image.invoke({"prompt": "x", "output_path": "../escape.png"})
    assert "inside project root" in out
