from craft_generator import generate_craft_xml, validate_payload


def test_validate_payload_accepts_valid_input():
    params = validate_payload(
        {
            "craftName": "Orbital_Test",
            "requestText": "хочу орбітальну ракету для запуску супутника",
        }
    )

    assert params["craft_name"] == "Orbital_Test"
    assert params["profile_id"] == "orbital_launcher"
    assert params["fuel_capacity"] >= 18000


def test_validate_payload_detects_ballistic_missile_intent():
    params = validate_payload(
        {
            "craftName": "Ballistic_Test",
            "requestText": "хочу зробити балістичну ракету",
        }
    )

    assert params["profile_id"] == "ballistic_missile"


def test_validate_payload_detects_generic_rocket_as_launcher():
    params = validate_payload(
        {
            "craftName": "Lift_Test",
            "requestText": "хочу просту ракету яка може нормально злетіти",
        }
    )

    assert params["profile_id"] == "orbital_launcher"


def test_validate_payload_detects_interceptor_intent():
    params = validate_payload(
        {
            "craftName": "THAAD_Test",
            "requestText": "хочу швидкий перехоплювач thaad для балістичних цілей",
        }
    )

    assert params["profile_id"] == "thaad"
    assert params["thrust"] > 420000


def test_validate_payload_extracts_variant_and_theme_from_request():
    params = validate_payload(
        {
            "craftName": "Strike_Test",
            "requestText": "зроби балістичну ракету іскандер-м на профі рівні оливковий і темно-сірий",
        }
    )

    assert params["profile_id"] == "ballistic_missile"
    assert params["variant_name"] == "Iskander-M"
    assert params["parser_source"] == "local"
    assert params["theme"]["base"] == "556B2F"
    assert params["theme"]["detail"] == "39424E"
    assert params["style_preset"] == "military_strike"


def test_validate_payload_detects_patriot_replica_copy_request():
    params = validate_payload(
        {
            "craftName": "Patriot_Copy",
            "requestText": "зроби прям копію patrroit",
        }
    )

    assert params["profile_id"] == "patriot_pac3"
    assert params["variant_name"] == "Patriot PAC-3"
    assert params["replica_mode"] is True
    assert params["style_preset"] == "replica"
    assert params["template_id"] == "patriot_pac3"
    assert params["prefer_template"] is True
    assert "не точна 1:1" in params["fidelity_note"]


def test_generate_uses_template_when_present(tmp_path, monkeypatch):
    template_dir = tmp_path / "library"
    template_dir.mkdir()
    template_file = template_dir / "thaad.xml"
    template_file.write_text(
        '<Craft name="TemplateTHAAD" xmlVersion="14"><Assembly /></Craft>',
        encoding="utf-8",
    )
    monkeypatch.setenv("CRAFT_TEMPLATE_DIR", str(template_dir))

    xml = generate_craft_xml(
        {
            "craft_name": "THAAD_Exact",
            "profile_id": "thaad",
            "variant_name": "THAAD",
            "request_text": "дуже чіткий thaad",
            "template_id": "thaad",
            "prefer_template": True,
            "thrust": 420000,
            "fuel_capacity": 7600,
            "stages": 2,
            "drag_scale": 0.22,
            "mass_scale": 0.84,
        }
    )

    assert '<Craft name="THAAD_Exact"' in xml
    assert '<Assembly />' in xml


def test_generate_ultra_detail_without_template_adds_many_segments():
    params = validate_payload(
        {
            "craftName": "THAAD_Auto",
            "requestText": "зроби дуже четкий thaad з ракетами aim-9",
        }
    )

    xml = generate_craft_xml(params)
    assert params["segment_count"] >= 7
    assert xml.count('partType="Fuselage1"') >= 7


def test_validate_payload_detects_davids_sling_style_request():
    params = validate_payload(
        {
            "craftName": "Sling_Test",
            "requestText": "зроби david's sling з ракетами aim-9",
        }
    )

    assert params["profile_id"] == "patriot_pac3"
    assert params["variant_name"] == "David's Sling Battery"
    assert params["segment_count"] >= 34
    assert params["prefer_template"] is True
    assert params["layout"] == "battery_launcher"


def test_validate_payload_detects_minimum_10k_lines_requirement():
    params = validate_payload(
        {
            "craftName": "Huge_XML",
            "requestText": "зроби thaad мінімум 10к рядків",
        }
    )

    assert params["min_output_lines"] == 10000
    assert params["segment_count"] >= 42


def test_validate_payload_detects_thaad_11mach_and_200km_request():
    params = validate_payload(
        {
            "craftName": "THAAD_Intercept",
            "requestText": "ракети thaad з радаром перехват до 11махів висота 200км",
        }
    )

    assert params["profile_id"] == "thaad"
    assert params["target_intercept_mach"] == 11
    assert params["target_intercept_altitude_km"] == 200
    assert params["layout"] == "battery_launcher"


def test_validate_payload_detects_minimum_20k_lines_requirement():
    params = validate_payload(
        {
            "craftName": "Huge_XML_20K",
            "requestText": "зроби маленькі ракети thaad з радаром мінімум 20к рядків",
        }
    )

    assert params["min_output_lines"] == 20000
    assert params["segment_count"] >= 56


def test_generate_real_20k_output_without_comment_padding():
    params = validate_payload(
        {
            "craftName": "THAAD_Real_20K",
            "requestText": "все разом маленькі ракети thaad з радаром до 11махів висота 200км мінімум 20к всі реальні рядки",
        }
    )

    xml = generate_craft_xml(params)
    assert params["real_output_lines"] is True
    assert len(xml.splitlines()) >= 20000
    assert "detail-pad:" not in xml
    assert xml.count('name="Internal Detail Cell"') > 1000


def test_generate_battery_launcher_compact_mode_scales_down_tubes():
    params = validate_payload(
        {
            "craftName": "THAAD_Compact",
            "requestText": "зроби маленькі ракети thaad не такі великі",
        }
    )

    xml = generate_craft_xml(params)
    assert params["size_multiplier"] == 0.62
    assert 'name="Launch Tube"' in xml
    assert xml.count('name="Launch Tube"') >= 8


def test_generate_respects_minimum_10k_output_lines():
    params = validate_payload(
        {
            "craftName": "Huge_XML",
            "requestText": "зроби thaad мінімум 10к рядків",
        }
    )

    xml = generate_craft_xml(params)
    assert len(xml.splitlines()) >= 10000


def test_generate_battery_launcher_layout_has_clustered_tubes():
    params = validate_payload(
        {
            "craftName": "Battery_Test",
            "requestText": "зроби david's sling як на фото",
        }
    )

    xml = generate_craft_xml(params)
    assert 'name="Launch Tube"' in xml
    assert xml.count('name="Launch Tube"') >= 4
    assert 'name="Tower"' in xml or 'name="Radar Mast"' in xml


def test_generate_craft_xml_includes_profile_specific_systems():
    xml = generate_craft_xml(
        {
            "craft_name": "THAAD_Test",
            "profile_id": "thaad",
            "variant_name": "THAAD",
            "request_text": "хочу швидкий перехоплювач thaad для балістичних цілей",
            "thrust": 420000,
            "fuel_capacity": 7600,
            "stages": 2,
            "drag_scale": 0.22,
            "mass_scale": 0.84,
            "theme": {"base": "F3F4F6", "detail": "7C8794", "accent": "B42318"},
        }
    )

    assert '<Craft name="THAAD"' in xml
    assert '<Assembly>' in xml
    assert '<Parts>' in xml
    assert 'partType="RocketEngine1"' in xml
    assert 'xmlVersion="14"' in xml
    assert '<Metadata>' not in xml
    assert 'color="B42318"' in xml
