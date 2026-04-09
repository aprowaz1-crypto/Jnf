from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request

from .profiles import PROFILES


OPENAI_API_URL = "https://api.openai.com/v1/responses"
DEFAULT_OPENAI_MODEL = "gpt-5.4"

COLOR_ALIASES = {
    "білий": "F3F4F6",
    "white": "F3F4F6",
    "сірий": "7C8794",
    "сiрий": "7C8794",
    "gray": "7C8794",
    "grey": "7C8794",
    "темно-сірий": "39424E",
    "темно сірий": "39424E",
    "dark gray": "39424E",
    "чорний": "1F2933",
    "black": "1F2933",
    "червоний": "B42318",
    "red": "B42318",
    "синій": "2457C5",
    "blue": "2457C5",
    "блакитний": "178BFF",
    "olive": "556B2F",
    "оливковий": "556B2F",
    "оливковo": "556B2F",
    "зелений": "3E7C59",
    "green": "3E7C59",
    "пісочний": "B38B59",
    "sand": "B38B59",
    "gold": "C99700",
    "золотий": "C99700",
    "orange": "D94F04",
    "помаранчевий": "D94F04",
}

VARIANT_HINTS = {
    "iskander-m": {
        "profile_id": "ballistic_missile",
        "variant_name": "Iskander-M",
        "style_preset": "military_strike",
        "template_id": "iskander_m",
        "theme": {"base": "556B2F", "detail": "39424E", "accent": "D94F04"},
    },
    "іскандер-м": {
        "profile_id": "ballistic_missile",
        "variant_name": "Iskander-M",
        "style_preset": "military_strike",
        "template_id": "iskander_m",
        "theme": {"base": "556B2F", "detail": "39424E", "accent": "D94F04"},
    },
    "іскандер": {
        "profile_id": "ballistic_missile",
        "variant_name": "Iskander-M",
        "style_preset": "military_strike",
        "template_id": "iskander_m",
        "theme": {"base": "556B2F", "detail": "39424E", "accent": "D94F04"},
    },
    "thaad": {
        "profile_id": "thaad",
        "variant_name": "THAAD",
        "style_preset": "defense_clean",
        "template_id": "thaad",
        "theme": {"base": "F3F4F6", "detail": "7C8794", "accent": "B42318"},
    },
    "patriot": {
        "profile_id": "patriot_pac3",
        "variant_name": "Patriot PAC-3",
        "style_preset": "defense_clean",
        "template_id": "patriot_pac3",
        "theme": {"base": "E5E7EB", "detail": "39424E", "accent": "B42318"},
    },
    "patrriot": {
        "profile_id": "patriot_pac3",
        "variant_name": "Patriot PAC-3",
        "style_preset": "defense_clean",
        "template_id": "patriot_pac3",
        "theme": {"base": "E5E7EB", "detail": "39424E", "accent": "B42318"},
    },
    "patrroit": {
        "profile_id": "patriot_pac3",
        "variant_name": "Patriot PAC-3",
        "style_preset": "defense_clean",
        "template_id": "patriot_pac3",
        "theme": {"base": "E5E7EB", "detail": "39424E", "accent": "B42318"},
    },
    "pac-3": {
        "profile_id": "patriot_pac3",
        "variant_name": "Patriot PAC-3",
        "style_preset": "defense_clean",
        "template_id": "patriot_pac3",
        "theme": {"base": "E5E7EB", "detail": "39424E", "accent": "B42318"},
    },
    "david": {
        "profile_id": "patriot_pac3",
        "variant_name": "David's Sling Battery",
        "style_preset": "ultra_detail",
        "template_id": "davids_sling",
        "theme": {"base": "DADADA", "detail": "5B6168", "accent": "8A8F96"},
    },
    "sling": {
        "profile_id": "patriot_pac3",
        "variant_name": "David's Sling Battery",
        "style_preset": "ultra_detail",
        "template_id": "davids_sling",
        "theme": {"base": "DADADA", "detail": "5B6168", "accent": "8A8F96"},
    },
    "davids sling": {
        "profile_id": "patriot_pac3",
        "variant_name": "David's Sling Battery",
        "style_preset": "ultra_detail",
        "template_id": "davids_sling",
        "theme": {"base": "DADADA", "detail": "5B6168", "accent": "8A8F96"},
    },
    "david's sling": {
        "profile_id": "patriot_pac3",
        "variant_name": "David's Sling Battery",
        "style_preset": "ultra_detail",
        "template_id": "davids_sling",
        "theme": {"base": "DADADA", "detail": "5B6168", "accent": "8A8F96"},
    },
}


def _extract_colors(text: str) -> dict[str, str]:
    matches: list[tuple[int, int, str]] = []
    for alias, hex_color in COLOR_ALIASES.items():
        index = text.find(alias)
        if index >= 0:
            matches.append((index, -len(alias), hex_color))

    matches.sort()

    found: list[str] = []
    for _, _, hex_color in matches:
        if hex_color not in found:
            found.append(hex_color)

    if not found:
        return {}

    theme: dict[str, str] = {"base": found[0]}
    if len(found) > 1:
        theme["detail"] = found[1]
    if len(found) > 2:
        theme["accent"] = found[2]
    return theme


def _local_directives(craft_name: str, request_text: str) -> dict[str, Any]:
    normalized = f"{craft_name} {request_text}".lower()
    directives: dict[str, Any] = {"parser_source": "local"}

    for alias, variant in VARIANT_HINTS.items():
        if alias in normalized:
            directives.update(variant)
            break

    theme = _extract_colors(normalized)
    if theme:
        directives["theme"] = {**directives.get("theme", {}), **theme}

    if any(word in normalized for word in ("pro", "профі", "профи", "круто", "красив", "реаліст", "детал")):
        directives.setdefault("style_preset", "showcase")

    if any(word in normalized for word in ("дуже чіт", "дуже чет", "ultra", "max detail", "максимально реаліст")):
        directives["style_preset"] = "ultra_detail"
        directives["segment_count"] = 30

    if any(word in normalized for word in ("копі", "копию", "copy", "replica", "1:1", "один в один")):
        directives["replica_mode"] = True
        directives["style_preset"] = "replica"
        directives["segment_count"] = max(22, int(directives.get("segment_count", 0)))
        directives["fidelity_note"] = (
            "Replica-style: візуально і параметрично максимально близько, "
            "але без оригінального XML-шаблону це не точна 1:1 копія."
        )

    if any(word in normalized for word in ("aim-9", "aim9", "sidewinder", "ракетами", "багато ракет")):
        directives["segment_count"] = max(24, int(directives.get("segment_count", 0)))
        directives.setdefault("style_preset", "ultra_detail")

    if any(word in normalized for word in ("david", "sling", "батаре", "пускова установка", "launcher battery")):
        directives["segment_count"] = max(34, int(directives.get("segment_count", 0)))
        directives["stages"] = 1
        directives["prefer_template"] = True
        directives["layout"] = "battery_launcher"
        directives.setdefault(
            "fidelity_note",
            "Для 1:1 David's Sling потрібен XML-шаблон. Без шаблону згенеровано auto-procedural батарейний стиль.",
        )

    if any(word in normalized for word in ("як на фото", "на фото", "photo style", "виглядала як")):
        directives.setdefault("layout", "battery_launcher")

    if any(word in normalized for word in ("маленьк", "не такі велик", "не такi велик", "small", "compact", "компакт")):
        directives["size_multiplier"] = 0.62
        directives.setdefault("layout", "battery_launcher")

    if any(word in normalized for word in ("10к", "10k", "10000", "10 000", "мінімум 10", "minimum 10k")):
        directives["min_output_lines"] = 10000
        directives["style_preset"] = "ultra_detail"
        directives["segment_count"] = max(42, int(directives.get("segment_count", 0)))
        directives.setdefault(
            "fidelity_note",
            "Увімкнено large-output режим: XML буде доповнено до щонайменше 10000 рядків.",
        )

    if any(word in normalized for word in ("20к", "20k", "20000", "20 000", "мінімум 20", "minimum 20k")):
        directives["min_output_lines"] = 20000
        directives["style_preset"] = "ultra_detail"
        directives["segment_count"] = max(56, int(directives.get("segment_count", 0)))
        directives.setdefault(
            "fidelity_note",
            "Увімкнено large-output режим: XML буде доповнено до щонайменше 20000 рядків.",
        )

    if any(word in normalized for word in ("всі реальні", "все реальні", "реальні рядки", "без падд", "без коментар", "real lines")):
        directives["real_output_lines"] = True

    if any(word in normalized for word in ("11мах", "11 мах", "mach 11", "11 mach")):
        directives["profile_id"] = "thaad"
        directives["variant_name"] = "THAAD Radar Interceptor"
        directives.setdefault("style_preset", "defense_clean")
        directives.setdefault("layout", "battery_launcher")
        directives["target_intercept_mach"] = 11
        directives["thrust_multiplier"] = max(1.15, float(directives.get("thrust_multiplier", 1.0)))

    if any(word in normalized for word in ("200км", "200 км", "200km", "200 km", "висота 200")):
        directives["profile_id"] = "thaad"
        directives.setdefault("variant_name", "THAAD Radar Interceptor")
        directives.setdefault("layout", "battery_launcher")
        directives["target_intercept_altitude_km"] = 200
        directives["fuel_multiplier"] = max(1.12, float(directives.get("fuel_multiplier", 1.0)))

    if directives.get("style_preset") in {"replica", "ultra_detail"} and directives.get("template_id"):
        directives["prefer_template"] = True

    if any(word in normalized for word in ("дуже швидк", "максимальн", "supersonic", "швидкий")):
        directives["thrust_multiplier"] = 1.08

    if any(word in normalized for word in ("далек", "long range", "дальність", "дальн")):
        directives["fuel_multiplier"] = 1.1

    if "3 ступ" in normalized or "триступ" in normalized:
        directives["stages"] = 3
    elif "2 ступ" in normalized or "двоступ" in normalized:
        directives["stages"] = 2
    elif "1 ступ" in normalized or "одноступ" in normalized:
        directives["stages"] = 1

    return directives


def _extract_json_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    output = payload.get("output")
    if not isinstance(output, list):
        return None

    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "output_text" and isinstance(block.get("text"), str):
                text = block["text"].strip()
                if text:
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        continue
    return None


def _call_openai(craft_name: str, request_text: str) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    prompt = (
        "You are extracting structured craft directives for a Juno: New Origins XML generator. "
        "Return JSON only with optional keys: profile_id, variant_name, style_preset, stages, "
        "segment_count, min_output_lines, thrust_multiplier, fuel_multiplier, theme, template_id, prefer_template, replica_mode, fidelity_note. "
        "theme must be an object with optional base/detail/accent six-digit uppercase hex colors. "
        f"Known profile ids: {', '.join(sorted(PROFILES))}. "
        f"Craft name: {craft_name}. Request: {request_text}."
    )
    body = {
        "model": model,
        "input": prompt,
        "text": {"format": {"type": "json_object"}},
    }
    data = json.dumps(body).encode("utf-8")
    req = request.Request(
        OPENAI_API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, error.URLError, error.HTTPError, json.JSONDecodeError):
        return None

    parsed = _extract_json_payload(payload)
    if not parsed:
        return None

    parsed["parser_source"] = "openai"
    if parsed.get("replica_mode"):
        parsed.setdefault(
            "fidelity_note",
            "Replica-style: візуально і параметрично максимально близько, але без оригінального XML-шаблону це не точна 1:1 копія.",
        )
    return parsed


def parse_request_directives(craft_name: str, request_text: str) -> dict[str, Any]:
    directives = _local_directives(craft_name, request_text)
    remote = _call_openai(craft_name, request_text)
    if not remote:
        return directives

    merged = {**directives, **remote}
    if isinstance(directives.get("theme"), dict) and isinstance(remote.get("theme"), dict):
        merged["theme"] = {**directives["theme"], **remote["theme"]}
    return merged