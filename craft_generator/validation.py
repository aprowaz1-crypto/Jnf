from __future__ import annotations

from typing import Any

from .inference import infer_parameters


def _require_string(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Поле '{field_name}' є обов'язковим.")
    return text


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    craft_name = _require_string(payload.get("craftName"), "Назва крафту")
    request_text = _require_string(payload.get("requestText"), "Опис того, що треба згенерувати")
    return infer_parameters(craft_name, request_text)
