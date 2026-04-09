from __future__ import annotations

import os
from io import BytesIO

from flask import Flask, jsonify, render_template, request, send_file

from craft_generator import generate_craft_xml, validate_payload
from craft_generator.template_library import has_template

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


def _parser_capabilities() -> dict[str, str | bool]:
    ai_enabled = bool(os.getenv("OPENAI_API_KEY"))
    return {
        "ai_enabled": ai_enabled,
        "model": os.getenv("OPENAI_MODEL", "gpt-5.4") if ai_enabled else "local-fallback",
    }


def _analysis_payload(params: dict[str, object]) -> dict[str, object]:
    theme = params.get("theme") if isinstance(params.get("theme"), dict) else {}
    template_id = str(params.get("template_id") or "")
    return {
        "craft_name": params.get("craft_name"),
        "variant_name": params.get("variant_name"),
        "profile_id": params.get("profile_id"),
        "profile_label": params.get("profile_label"),
        "style_preset": params.get("style_preset"),
        "template_id": template_id,
        "template_available": has_template(template_id),
        "prefer_template": params.get("prefer_template"),
        "replica_mode": params.get("replica_mode"),
        "fidelity_note": params.get("fidelity_note"),
        "parser_source": params.get("parser_source"),
        "stages": params.get("stages"),
        "thrust": params.get("thrust"),
        "fuel_capacity": params.get("fuel_capacity"),
        "size_multiplier": params.get("size_multiplier"),
        "target_intercept_mach": params.get("target_intercept_mach"),
        "target_intercept_altitude_km": params.get("target_intercept_altitude_km"),
        "theme": theme,
        "capabilities": _parser_capabilities(),
    }


@app.post("/api/analyze")
def analyze():
    payload = request.get_json(silent=True) or request.form.to_dict()

    try:
        params = validate_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc), "capabilities": _parser_capabilities()}), 400

    return jsonify(_analysis_payload(params))


@app.post("/api/generate")
def generate():
    payload = request.get_json(silent=True) or request.form.to_dict()

    try:
        params = validate_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    xml_content = generate_craft_xml(params)
    filename = f"{params['craft_name'].replace(' ', '_')}.xml"
    xml_bytes = BytesIO(xml_content.encode("utf-8"))

    return send_file(
        xml_bytes,
        mimetype="application/xml",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
