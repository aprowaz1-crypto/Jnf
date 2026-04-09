from app import app


def test_analyze_endpoint_returns_structured_preview(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    client = app.test_client()
    response = client.post(
        "/api/analyze",
        json={
            "craftName": "Strike_Test",
            "requestText": "зроби балістичну ракету іскандер-м на профі рівні оливковий і темно-сірий",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["profile_id"] == "ballistic_missile"
    assert payload["variant_name"] == "Iskander-M"
    assert payload["parser_source"] == "local"
    assert payload["capabilities"]["ai_enabled"] is False


def test_analyze_endpoint_validates_required_fields():
    client = app.test_client()
    response = client.post("/api/analyze", json={"craftName": "Only_Name"})

    assert response.status_code == 400
    payload = response.get_json()
    assert "error" in payload
    assert "capabilities" in payload


def test_analyze_endpoint_reports_replica_constraints():
    client = app.test_client()
    response = client.post(
        "/api/analyze",
        json={
            "craftName": "Patriot_Copy",
            "requestText": "зроби прям копію patrroit",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["profile_id"] == "patriot_pac3"
    assert payload["replica_mode"] is True
    assert payload["template_id"] == "patriot_pac3"
    assert payload["prefer_template"] is True
    assert payload["template_available"] is False
    assert "не точна 1:1" in payload["fidelity_note"]


def test_analyze_endpoint_reports_intercept_targets_and_size():
    client = app.test_client()
    response = client.post(
        "/api/analyze",
        json={
            "craftName": "THAAD_Compact",
            "requestText": "маленькі ракети thaad з радаром перехват до 11махів висота 200км",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["profile_id"] == "thaad"
    assert payload["size_multiplier"] == 0.62
    assert payload["target_intercept_mach"] == 11
    assert payload["target_intercept_altitude_km"] == 200