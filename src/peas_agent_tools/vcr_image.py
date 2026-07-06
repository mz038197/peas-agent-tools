"""Vans Coding Router image generation (POST /v1/images)."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import httpx

from peas_agent_tools.config import get_settings
from peas_agent_tools.paths import resolve_project_path

DEFAULT_BASE_URL = "https://ai.vanscoding.com/v1"
DEFAULT_MODEL = "openrouter@black-forest-labs/flux.2-klein-4b"
DEFAULT_EDIT_MODEL = "openrouter@openai/gpt-5.4-image-2"
DEFAULT_PRESETS: dict[str, str] = {
    "icon": "openrouter@black-forest-labs/flux.2-klein-4b",
    "ui_mockup": "openrouter@openai/gpt-5.4-image-2",
    "photo": "openrouter@bytedance-seed/seedream-4.5",
}
MODEL_REF_LIMITS: dict[str, int] = {
    "openrouter@openai/gpt-5.4-image-2": 16,
    "openrouter@openai/gpt-5-image": 16,
    "openrouter@openai/gpt-5-image-mini": 16,
    "openrouter@google/gemini-3.1-flash-image": 14,
    "openrouter@bytedance-seed/seedream-4.5": 14,
    "openrouter@black-forest-labs/flux.2-klein-4b": 4,
    "openrouter@black-forest-labs/flux.2-pro": 8,
}

PresetName = Literal["icon", "ui_mockup", "photo"]


@dataclass
class ImageSettings:
    enable: bool = True
    api_key: str = ""
    base_url: str = DEFAULT_BASE_URL
    timeout: int = 120


_IMAGE_SETTINGS = ImageSettings()


def configure_image(config: dict[str, Any]) -> None:
    """Load tools.image settings from peas-tools.json (or configure_tools)."""
    global _IMAGE_SETTINGS
    tools = config.get("tools") if isinstance(config.get("tools"), dict) else {}
    image = tools.get("image") if isinstance(tools.get("image"), dict) else {}

    def _str(d: dict[str, Any], *keys: str, default: str = "") -> str:
        for key in keys:
            val = d.get(key)
            if isinstance(val, str):
                return val
        return default

    def _bool(d: dict[str, Any], *keys: str, default: bool = True) -> bool:
        for key in keys:
            if key in d:
                return bool(d[key])
        return default

    def _int(d: dict[str, Any], *keys: str, default: int) -> int:
        for key in keys:
            val = d.get(key)
            try:
                return int(val)
            except (TypeError, ValueError):
                continue
        return default

    base = _str(image, "baseUrl", "base_url", default=DEFAULT_BASE_URL) or DEFAULT_BASE_URL
    _IMAGE_SETTINGS = ImageSettings(
        enable=_bool(image, "enable", default=True),
        api_key=_str(image, "apiKey", "api_key"),
        base_url=base.rstrip("/"),
        timeout=max(1, _int(image, "timeout", default=120)),
    )


def get_image_settings() -> ImageSettings:
    return _IMAGE_SETTINGS


def _resolve_api_key() -> str:
    key = (_IMAGE_SETTINGS.api_key or "").strip()
    if key:
        return key
    env_key = os.environ.get("VSROUTER_API_KEY", "").strip()
    if env_key:
        return env_key
    return ""


def image_tools_enabled() -> bool:
    return _IMAGE_SETTINGS.enable and bool(_resolve_api_key())


def _resolve_base_url() -> str:
    for env_key in ("VCR_BASE_URL", "OPENAI_BASE_URL"):
        value = os.environ.get(env_key, "").strip()
        if value:
            return value.rstrip("/")
    return _IMAGE_SETTINGS.base_url.rstrip("/") or DEFAULT_BASE_URL


def _resolve_model(
    *,
    model: str | None,
    preset: str | None,
    reference_paths: list[Path],
) -> str:
    if model and model.strip():
        return model.strip()
    if reference_paths:
        return DEFAULT_EDIT_MODEL
    if preset:
        chosen = DEFAULT_PRESETS.get(preset)
        if chosen:
            return chosen
        raise ValueError(f"Unknown preset: {preset}")
    env_model = os.environ.get("VCR_IMAGE_MODEL", "").strip()
    if env_model:
        return env_model
    return DEFAULT_MODEL


def _max_references(model: str) -> int:
    return MODEL_REF_LIMITS.get(model, 4)


def _mime_for_path(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    if guessed in {"image/png", "image/jpeg", "image/webp", "image/gif"}:
        return guessed
    mapping = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    mime = mapping.get(path.suffix.lower())
    if not mime:
        raise ValueError(f"Unsupported image type: {path}")
    return mime


def _encode_reference(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Reference image not found: {path}")
    mime = _mime_for_path(path)
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{b64}"},
    }


def _resolve_output_path(output_path: str) -> Path:
    path = output_path.strip() or "assets/generated/image.png"
    target = resolve_project_path(path)
    root = get_settings().project_root.resolve()
    if root not in target.parents and target != root:
        raise ValueError(f"Output path must be inside project root: {root}")
    return target


def _parse_error_body(raw: str) -> str:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(payload, dict):
        err = payload.get("error")
        if isinstance(err, dict):
            parts = [str(err.get("message", ""))]
            code = err.get("code")
            if code:
                parts.append(f"code={code}")
            return " ".join(p for p in parts if p)
        detail = payload.get("detail")
        if detail:
            return str(detail)
    return json.dumps(payload, ensure_ascii=False)


def _post_images(url: str, api_key: str, body: dict[str, Any], timeout_sec: int) -> dict[str, Any]:
    try:
        response = httpx.post(
            url,
            json=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            timeout=timeout_sec,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        message = _parse_error_body(exc.response.text)
        raise RuntimeError(f"HTTP {exc.response.status_code}: {message}") from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected response shape from /v1/images")
    return payload


def _extract_b64(response: dict[str, Any]) -> bytes:
    data = response.get("data")
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            b64 = first.get("b64_json")
            if isinstance(b64, str) and b64:
                return base64.b64decode(b64)
    raise RuntimeError("Response missing data[0].b64_json")


def generate_vcr_image(
    *,
    prompt: str,
    output_path: str = "assets/generated/image.png",
    preset: str | None = None,
    model: str = "",
    aspect_ratio: str = "",
    resolution: str = "",
    reference_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Generate an image via VCR; write to project path; return result metadata."""
    text = (prompt or "").strip()
    if not text:
        raise ValueError("prompt is required")

    api_key = _resolve_api_key()
    if not api_key:
        raise ValueError(
            "Missing API key. Set tools.image.apiKey in peas-tools.json "
            "or VSROUTER_API_KEY (vcr_sk_... from Portal)."
        )

    refs = [resolve_project_path(p) for p in (reference_paths or [])]
    chosen_model = _resolve_model(model=model or None, preset=preset, reference_paths=refs)
    max_refs = _max_references(chosen_model)
    if len(refs) > max_refs:
        refs = refs[:max_refs]

    output_file = _resolve_output_path(output_path)
    root = get_settings().project_root.resolve()

    body: dict[str, Any] = {"model": chosen_model, "prompt": text}
    if aspect_ratio.strip():
        body["aspect_ratio"] = aspect_ratio.strip()
    if resolution.strip():
        body["resolution"] = resolution.strip()
    if refs:
        body["input_references"] = [_encode_reference(p) for p in refs]

    base_url = _resolve_base_url()
    url = f"{base_url.rstrip('/')}/images"
    timeout = _IMAGE_SETTINGS.timeout
    if refs:
        timeout = max(timeout, 180)

    response = _post_images(url, api_key, body, timeout)
    image_bytes = _extract_b64(response)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_bytes(image_bytes)

    usage = response.get("usage") if isinstance(response.get("usage"), dict) else {}
    rel_output = output_file.relative_to(root).as_posix()
    ref_rel = [p.relative_to(root).as_posix() for p in refs]
    return {
        "path": rel_output,
        "model": chosen_model,
        "total_tokens": int(usage.get("total_tokens") or 0),
        "reference_paths": ref_rel,
    }
