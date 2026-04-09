from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .ai_parser import parse_request_directives
from .profiles import PROFILES, CraftProfile


KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("thaad", ("thaad", "thad", "протиракет", "перехоп")),
    ("ballistic_missile", ("балістична ракета", "балістичн", "ballistic missile", "балістич")),
    ("patriot_pac3", ("patriot", "pac-3", "pac3")),
    ("interceptor_10mach", ("10 mach", "10mach", "гіперзву", "мах 10")),
    ("orbital_launcher", ("орбі", "носі", "launcher", "payload", "супутник", "ракета-носій")),
    ("sounding_rocket", ("дослід", "suborb", "sub-orb", "тест", "навч", "sounding")),
    ("orbital_tug", ("tug", "буксир", "стику", "маневр", "орбітальн")),
]


def _pick_profile(request_text: str) -> CraftProfile:
    normalized = request_text.lower()

    if "баліст" in normalized and any(word in normalized for word in ("ракет", "missile")):
        if not any(word in normalized for word in ("thaad", "перехоп", "протиракет", "pac-3", "patriot")):
            return PROFILES["ballistic_missile"]

    if any(word in normalized for word in ("ракет", "launcher", "launch", "злет", "старт")):
        if not any(word in normalized for word in ("thaad", "перехоп", "протиракет", "patriot", "pac-3", "pac3", "баліст", "орбі", "буксир")):
            return PROFILES["orbital_launcher"]

    for profile_id, hints in KEYWORDS:
        if any(hint in normalized for hint in hints):
            return PROFILES[profile_id]
    return PROFILES["orbital_launcher"]


def infer_parameters(craft_name: str, request_text: str) -> dict[str, Any]:
    directives = parse_request_directives(craft_name, request_text)
    profile_id = str(directives.get("profile_id") or _pick_profile(request_text).profile_id)
    profile = PROFILES[profile_id]
    normalized = request_text.lower()

    stages = int(directives.get("stages") or profile.stages)
    if "одноступ" in normalized or "1 ступ" in normalized:
        stages = 1
    elif "двоступ" in normalized or "2 ступ" in normalized:
        stages = 2
    elif "3 ступ" in normalized or "триступ" in normalized:
        stages = 3

    segment_count = int(directives.get("segment_count") or 1)
    segment_count = max(1, min(segment_count, 80))

    size_multiplier = float(directives.get("size_multiplier") or 1.0)
    size_multiplier = max(0.35, min(size_multiplier, 1.6))

    min_output_lines = int(directives.get("min_output_lines") or 0)
    min_output_lines = max(0, min(min_output_lines, 50000))

    thrust = profile.thrust
    if any(word in normalized for word in ("швидк", "fast", "speed", "гіпер")):
        thrust = int(thrust * 1.12)
    if any(word in normalized for word in ("легк", "small", "compact", "компакт")):
        thrust = int(thrust * 0.88)
    thrust = int(thrust * float(directives.get("thrust_multiplier", 1.0)))

    fuel_capacity = profile.fuel_capacity
    if any(word in normalized for word in ("далек", "long", "дальн", "орбіт")):
        fuel_capacity = int(fuel_capacity * 1.18)
    if any(word in normalized for word in ("коротк", "short", "ближ")):
        fuel_capacity = int(fuel_capacity * 0.82)
    fuel_capacity = int(fuel_capacity * float(directives.get("fuel_multiplier", 1.0)))

    drag_scale = profile.drag_scale
    if any(word in normalized for word in ("атмосфер", "maneuver", "маневр")):
        drag_scale = min(1.5, round(drag_scale + 0.04, 2))

    mass_scale = profile.mass_scale
    if any(word in normalized for word in ("важк", "heavy", "бронь")):
        mass_scale = min(2.0, round(mass_scale + 0.08, 2))
    if any(word in normalized for word in ("легк", "light", "compact", "компакт")):
        mass_scale = max(0.3, round(mass_scale - 0.06, 2))

    theme = directives.get("theme") if isinstance(directives.get("theme"), dict) else {}

    return {
        "craft_name": craft_name,
        "request_text": request_text,
        "profile_id": profile.profile_id,
        "profile_label": profile.label,
        "variant_name": directives.get("variant_name", profile.label),
        "style_preset": directives.get("style_preset", "default"),
        "layout": directives.get("layout", "single_stack"),
        "segment_count": segment_count,
        "size_multiplier": size_multiplier,
        "min_output_lines": min_output_lines,
        "real_output_lines": bool(directives.get("real_output_lines", False)),
        "template_id": directives.get("template_id", ""),
        "prefer_template": bool(directives.get("prefer_template", False)),
        "replica_mode": bool(directives.get("replica_mode", False)),
        "fidelity_note": directives.get("fidelity_note", ""),
        "parser_source": directives.get("parser_source", "heuristic"),
        "theme": theme,
        "thrust": thrust,
        "fuel_capacity": fuel_capacity,
        "stages": stages,
        "drag_scale": drag_scale,
        "mass_scale": mass_scale,
        "target_intercept_mach": directives.get("target_intercept_mach"),
        "target_intercept_altitude_km": directives.get("target_intercept_altitude_km"),
        "profile_defaults": asdict(profile),
    }
