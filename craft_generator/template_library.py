from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


_CRAFT_NAME_RE = re.compile(r'(<Craft\b[^>]*\bname=")(.*?)(")')


def _sanitize_name(craft_name: str) -> str:
    cleaned = " ".join(craft_name.split())
    return cleaned[:80] or "Generated Craft"


def _apply_craft_name(xml: str, craft_name: str) -> str:
    safe_name = _sanitize_name(craft_name).replace('"', "")
    return _CRAFT_NAME_RE.sub(rf'\1{safe_name}\3', xml, count=1)


def _template_root() -> Path:
    configured = os.getenv("CRAFT_TEMPLATE_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parent.parent / "templates" / "craft_library"


def has_template(template_id: str) -> bool:
    safe_id = str(template_id or "").strip().lower()
    if not safe_id:
        return False
    candidate = _template_root() / f"{safe_id}.xml"
    return candidate.exists() and candidate.is_file()


def load_template_xml(params: dict[str, Any]) -> str | None:
    template_id = str(params.get("template_id") or "").strip().lower()
    if not template_id:
        return None

    candidate = _template_root() / f"{template_id}.xml"
    if not candidate.exists() or not candidate.is_file():
        return None

    content = candidate.read_text(encoding="utf-8").strip()
    if "<Craft" not in content:
        return None

    craft_name = str(params.get("craft_name") or params.get("variant_name") or "Generated Craft")
    return _apply_craft_name(content, craft_name)