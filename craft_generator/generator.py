from __future__ import annotations

from xml.dom import minidom
from xml.etree import ElementTree as ET

from .profiles import PROFILES, CraftProfile
from .template_library import load_template_xml


THEME_MATERIALS = [
    {"name": "Base Color", "color": "FFFFFF", "m": "0.3", "s": "0"},
    {"name": "Detail Color", "color": "178BFF", "m": "0", "s": "0.3"},
    {"name": "Light Metal", "color": "CBCDCE", "m": "0.85", "s": "0.8"},
    {"name": "Heavy Metal", "color": "76736F", "m": "0.85", "s": "0.5"},
    {"name": "Ablative", "color": "000000", "m": "0.85", "s": "0", "d": "0.5"},
    {"name": "Accent Color 1", "color": "FFFFFF", "m": "0.1", "s": "0.08"},
    {"name": "Accent Color 2", "color": "FFFFFF", "m": "0.1", "s": "0.08"},
    {"name": "Accent Color 3", "color": "FFFFFF", "m": "0.1", "s": "0.08"},
    {"name": "Accent Color 4", "color": "FFFFFF", "m": "0.1", "s": "0.08"},
    {"name": "Accent Color 5", "color": "FFFFFF", "m": "0.1", "s": "0.08"},
    {"name": "Gauge Color 1", "color": "000000", "m": "0.85", "s": "0"},
    {"name": "Gauge Color 2", "color": "FF8000", "m": "0", "s": "0.5", "e": "1"},
    {"name": "Gauge Color 3", "color": "FFFFFF", "m": "0", "s": "0", "e": "1"},
    {"name": "Gauge Color 4", "color": "FF0000", "m": "0", "s": "0", "e": "1"},
    {"name": "Gauge Color 5", "color": "68D100", "m": "0", "s": "0", "e": "1"},
    {"name": "Fabric Base", "color": "FFFFFF", "m": "0", "s": "0", "d": "0.2"},
    {"name": "Fabric Detail", "color": "178BFF", "m": "0", "s": "0", "d": "0.1"},
    {"name": "Brushed Light Metal", "color": "CBCDCE", "m": "0.85", "s": "0.3", "d": "0.5"},
    {"name": "Brushed Heavy Metal", "color": "76736F", "m": "0.85", "s": "0.3", "d": "0.5"},
    {"name": "Sun Insulation", "color": "574204", "m": "0.95", "s": "0.95", "d": "0.2"},
    {"name": "Solar Cells", "color": "000046", "m": "0.85", "s": "0.5", "d": "0.1"},
    {"name": "Light", "color": "FFEEB9", "m": "0", "s": "1"},
    {"name": "Display", "color": "FFFFFF", "m": "0.1", "s": "0.08"},
    {"name": "Glass Exterior", "color": "FFFFFF", "m": "1", "s": "1", "t": "0.8"},
    {"name": "Glass Interior", "color": "808080", "m": "1", "s": "0", "t": "0.9"},
]

PROFILE_THEMES = {
    "ballistic_missile": {"base": "556B2F", "detail": "39424E", "accent": "D94F04"},
    "thaad": {"base": "F3F4F6", "detail": "7C8794", "accent": "B42318"},
    "patriot_pac3": {"base": "E5E7EB", "detail": "39424E", "accent": "B42318"},
    "interceptor_10mach": {"base": "D5D9E0", "detail": "20262E", "accent": "178BFF"},
    "orbital_launcher": {"base": "FFFFFF", "detail": "178BFF", "accent": "CBCDCE"},
    "sounding_rocket": {"base": "F4F1DE", "detail": "2457C5", "accent": "C99700"},
    "orbital_tug": {"base": "CBCDCE", "detail": "000046", "accent": "68D100"},
}


def _fmt(number: float) -> str:
    text = f"{number:.6f}".rstrip("0").rstrip(".")
    return text or "0"


def _geometry_preset(params: dict[str, int | float | str]) -> dict[str, float]:
    variant_name = str(params.get("variant_name", "")).lower()
    style_preset = str(params.get("style_preset", "default")).lower()
    replica_mode = bool(params.get("replica_mode", False))

    preset = {
        "fuselage_radius": 1.0,
        "fuselage_offset_y": 0.5216417,
        "fuselage_pos_y": -0.65,
        "engine_pos_y": -0.75,
        "tiling_x": 4.0,
        "tiling_y": 4.0,
        "engine_size_mul": 1.0,
        "nozzle_mul": 1.0,
    }

    if "patriot" in variant_name:
        preset.update(
            {
                "fuselage_radius": 0.82,
                "fuselage_offset_y": 0.44,
                "fuselage_pos_y": -0.60,
                "engine_pos_y": -0.70,
                "tiling_x": 5.2,
                "engine_size_mul": 0.86,
                "nozzle_mul": 0.84,
            }
        )
    elif "thaad" in variant_name:
        preset.update(
            {
                "fuselage_radius": 0.78,
                "fuselage_offset_y": 0.60,
                "fuselage_pos_y": -0.68,
                "engine_pos_y": -0.82,
                "tiling_x": 6.0,
                "engine_size_mul": 0.92,
                "nozzle_mul": 0.9,
            }
        )
    elif "iskander" in variant_name:
        preset.update(
            {
                "fuselage_radius": 1.08,
                "fuselage_offset_y": 0.48,
                "fuselage_pos_y": -0.58,
                "engine_pos_y": -0.68,
                "tiling_x": 4.8,
                "engine_size_mul": 1.12,
                "nozzle_mul": 1.08,
            }
        )

    if replica_mode or style_preset == "replica":
        preset["tiling_x"] = max(4.8, preset["tiling_x"])
        preset["tiling_y"] = 4.6
    return preset


def _segment_profile(params: dict[str, int | float | str], segment_count: int) -> list[dict[str, float]]:
    variant_name = str(params.get("variant_name", "")).lower()
    style_preset = str(params.get("style_preset", "default")).lower()

    if "thaad" in variant_name:
        nose, mid, tail = 0.38, 0.78, 0.52
    elif "patriot" in variant_name:
        nose, mid, tail = 0.34, 0.70, 0.46
    elif "iskander" in variant_name:
        nose, mid, tail = 0.50, 1.08, 0.72
    else:
        nose, mid, tail = 0.46, 0.92, 0.62

    if style_preset in {"ultra_detail", "replica"}:
        mid *= 1.12
        tail *= 1.06

    profile: list[float] = []
    for i in range(segment_count):
        t = i / max(1, segment_count - 1)
        if t < 0.22:
            # Nose cone transition.
            local = t / 0.22
            radius = nose + (mid - nose) * (local ** 1.6)
        elif t < 0.78:
            # Main body with mild wave so it is not a pure cylinder.
            local = (t - 0.22) / 0.56
            radius = mid * (0.96 + 0.08 * (1 - ((local * 2) - 1) ** 2))
        else:
            # Tail taper.
            local = (t - 0.78) / 0.22
            radius = mid - (mid - tail) * (local ** 1.2)
        profile.append(max(0.26, min(1.42, radius)))

    shaped: list[dict[str, float]] = []
    for i, radius in enumerate(profile):
        next_radius = profile[i + 1] if i + 1 < segment_count else profile[i] * 0.96
        previous_radius = profile[i - 1] if i > 0 else profile[i] * 0.94
        deformation_x = max(-0.18, min(0.18, (next_radius - previous_radius) * 0.45))
        shaped.append(
            {
                "top": max(0.24, min(1.5, next_radius)),
                "bottom": max(0.24, min(1.5, radius)),
                "deform_x": deformation_x,
            }
        )
    return shaped


def _ensure_minimum_lines(xml_text: str, minimum_lines: int) -> str:
    if minimum_lines <= 0:
        return xml_text

    lines = xml_text.splitlines()
    if len(lines) >= minimum_lines:
        return xml_text

    closing_tag = "</Craft>"
    close_index = xml_text.rfind(closing_tag)
    if close_index == -1:
        return xml_text

    needed = minimum_lines - len(lines)
    padding_lines = [f"  <!-- detail-pad:{index:05d} -->" for index in range(1, needed + 1)]
    padding = "\n".join(padding_lines) + "\n"
    return xml_text[:close_index] + padding + xml_text[close_index:]


def _resolve_theme(profile_id: str, params: dict[str, int | float | str]) -> list[dict[str, str]]:
    profile_theme = PROFILE_THEMES.get(profile_id, PROFILE_THEMES["orbital_launcher"])
    request_theme = params.get("theme") if isinstance(params.get("theme"), dict) else {}
    merged_theme = {**profile_theme, **request_theme}

    materials = [material.copy() for material in THEME_MATERIALS]
    for material in materials:
        if material["name"] == "Base Color":
            material["color"] = str(merged_theme.get("base", material["color"]))
        elif material["name"] == "Detail Color":
            material["color"] = str(merged_theme.get("detail", material["color"]))
        elif material["name"] == "Accent Color 1":
            material["color"] = str(merged_theme.get("accent", material["color"]))
        elif material["name"] == "Accent Color 2":
            material["color"] = str(merged_theme.get("detail", material["color"]))
        elif material["name"] == "Accent Color 3":
            material["color"] = str(merged_theme.get("base", material["color"]))
    return materials


def _add_materials(theme: ET.Element, materials: list[dict[str, str]]) -> None:
    for material in materials:
        ET.SubElement(theme, "Material", **material)


def _add_theme_section(root: ET.Element, profile_id: str, params: dict[str, int | float | str]) -> None:
    theme_name = str(params.get("variant_name") or params.get("profile_label") or "Custom")
    materials = _resolve_theme(profile_id, params)
    designer_settings = ET.SubElement(root, "DesignerSettings", themeName=theme_name)
    theme = ET.SubElement(designer_settings, "Theme", name=theme_name, id="25a9195c-c404-4c77-9ea1-eef798ccc505")
    _add_materials(theme, materials)

    themes = ET.SubElement(root, "Themes")
    theme_copy = ET.SubElement(themes, "Theme", name=theme_name, id="25a9195c-c404-4c77-9ea1-eef798ccc505")
    _add_materials(theme_copy, materials)
    ET.SubElement(root, "Symmetry")


def _command_pod(parts: ET.Element, profile: CraftProfile, params: dict[str, int | float | str]) -> None:
    part = ET.SubElement(
        parts,
        "Part",
        id="0",
        partType="CommandPod5",
        position="0,0.75,0",
        rotation="0,0,0",
        rootPart="true",
        commandPodId="0",
        materials="0,1,19,3,4",
        texture="Fuselage10",
    )
    ET.SubElement(part, "Drag", drag="2.095125,2.097336,0,0,2.123798,2.1238", area="2.867412,2.867412,0,0,2.902858,2.902858")
    ET.SubElement(part, "Config", centerOfMass="0,-0.125,0", heatShieldScale="0")
    command_pod = ET.SubElement(
        part,
        "CommandPod",
        activationGroupNames=",,,,,,,Landing Gear,Solar Panels,RCS",
        activationGroupStates="false,false,false,false,false,false,false,true,false,true",
        pidPitch="10,0,25",
        pidRoll="10,0,25",
        pilotSeatRotation="270,0,0",
        powerConsumption="60",
        stageCalculationVersion="1",
    )
    ET.SubElement(command_pod, "Controls")
    ET.SubElement(part, "Gyroscope", power=str(max(20, profile.max_g * 6)), powerScale="0")
    pod_capacity = max(1200, int(params["fuel_capacity"]) // 6)
    ET.SubElement(part, "FuelTank", capacity=str(pod_capacity), fuel=str(pod_capacity), subPriority="-2")
    ET.SubElement(part, "CrewCompartment", capacity="1")
    ET.SubElement(part, "ScalablePod", mass="10.8841038")


def _stage_separator(parts: ET.Element) -> None:
    part = ET.SubElement(
        parts,
        "Part",
        id="1",
        partType="Detacher1",
        position="0,0.05,0",
        rotation="0,0,0",
        name="Stage Detacher",
        activationStage="1",
        commandPodId="0",
        materials="0,0,0,0,0",
        texture="Fuselage10",
        textureTiling="0.5,1",
    )
    ET.SubElement(part, "Drag", drag="0.6027768,0.602836,0.005196117,0,0.5950093,0.5890096", area="0.7766947,0.7766947,0.01408514,0,0.7717359,0.7657378")
    ET.SubElement(part, "Config", autoActivateIfNoStageOrActivationGroup="false", heatShieldScale="0")
    ET.SubElement(part, "Fuselage", bottomScale="1,1", deadWeightPercentage="-10", deformations="0,0,0", depthCurve="0", offset="0,0.187839,0", topScale="1,1", version="2")
    ET.SubElement(part, "Detacher", force="0", version="2")
    ET.SubElement(part, "CoverEngine")
    ET.SubElement(part, "CrossFeed")


def _fuel_stage(
    parts: ET.Element,
    params: dict[str, int | float | str],
    part_id: int,
    position_y: float,
    stage_capacity: int,
    top_scale: float,
    bottom_scale: float,
    deform_x: float,
) -> None:
    geometry = _geometry_preset(params)
    top_bottom_scale = f"{_fmt(top_scale)},{_fmt(top_scale)}"
    bottom_pair = f"{_fmt(bottom_scale)},{_fmt(bottom_scale)}"
    texture_tiling = f"{_fmt(geometry['tiling_x'])},{_fmt(geometry['tiling_y'])}"
    deformations = f"{_fmt(deform_x)},0,0"
    part = ET.SubElement(
        parts,
        "Part",
        id=str(part_id),
        partType="Fuselage1",
        position=f"0,{_fmt(position_y)},0",
        rotation="0,0,0",
        name=f"Main Stage {part_id}",
        commandPodId="0",
        materials="18,4,4,0,0",
        texture="Fuselage10",
        textureTiling=texture_tiling,
    )
    ET.SubElement(part, "Drag", drag="1.623893,1.623893,0,0.185119,1.54042,1.517003", area="2.066535,2.066535,0,0.185119,2.012847,1.989357")
    ET.SubElement(part, "Config", heatShieldScale="0")
    ET.SubElement(
        part,
        "Fuselage",
        bottomScale=bottom_pair,
        deadWeightPercentage="0",
        deformations=deformations,
        depthCurve="0",
        fuelPercentage="0",
        offset=f"0,{_fmt(geometry['fuselage_offset_y'])},0",
        topScale=top_bottom_scale,
        version="2",
    )
    ET.SubElement(part, "FuelTank", capacity=str(stage_capacity), fuel=str(stage_capacity), fuelType="Monopropellant", subPriority="20")


def _engine(parts: ET.Element, profile: CraftProfile, params: dict[str, int | float | str], part_id: int, position_y: float) -> None:
    thrust = int(params["thrust"])
    geometry = _geometry_preset(params)
    engine_size = min(4.5, max(1.2, thrust / 180000))
    engine_size = min(4.5, max(1.0, engine_size * geometry["engine_size_mul"]))
    nozzle_size = min(6.0, max(2.0, engine_size * 1.8))
    nozzle_size = min(6.2, max(1.8, nozzle_size * geometry["nozzle_mul"]))
    throat_size = min(2.2, max(0.7, engine_size * 0.75))
    mass_flow_rate = max(25.0, thrust / 3200)

    part = ET.SubElement(
        parts,
        "Part",
        id=str(part_id),
        partType="RocketEngine1",
        position=f"0,{_fmt(position_y)},0",
        rotation="0,0,0",
        name="Engine",
        activationStage="0",
        commandPodId="0",
        materials="0,1,2,3,4",
        nozzleTexture="RocketEngine_Nozzle",
        nozzleExtensionTexture="RocketEngine_Extension2",
    )
    ET.SubElement(part, "Drag", drag="0.01055794,0.01055794,0,0.04856021,0.007324871,0.007324869", area="0.01408514,0.01408514,0,0.1167055,0.009996479,0.009996479")
    ET.SubElement(part, "Config", heatShieldScale="0")
    ET.SubElement(
        part,
        "RocketEngine",
        engineSubTypeId="PressureFed",
        engineTypeId="Monoprop",
        wattsPerFuelFlowOverride="-1",
        heatTransferOverride="1",
        fuelType="Monopropellant",
        mass=_fmt(0.0820701942 * float(params["mass_scale"])),
        thrustOverride=str(thrust),
        massFlowRateOverride=_fmt(mass_flow_rate),
        nozzleSize=_fmt(nozzle_size),
        nozzleThroatSize=_fmt(throat_size),
        price=str(max(12000, thrust // 18)),
        size=_fmt(engine_size),
        gimbalRange=str(profile.gimbal_range),
    )
    ET.SubElement(part, "InputController", inputId="Throttle")


def _assembly(root: ET.Element, profile: CraftProfile, params: dict[str, int | float | str]) -> None:
    if str(params.get("layout", "single_stack")) == "battery_launcher":
        _assembly_battery_launcher(root, profile, params)
        return

    assembly = ET.SubElement(root, "Assembly")
    parts = ET.SubElement(assembly, "Parts")
    _command_pod(parts, profile, params)

    segment_count = max(1, int(params.get("segment_count", 1)))
    total_capacity = max(1800, int(params["fuel_capacity"]))
    segment_capacity = max(500, total_capacity // segment_count)

    geometry = _geometry_preset(params)
    base_y = float(geometry["fuselage_pos_y"])
    spacing = 0.88
    segment_shape_profile = _segment_profile(params, segment_count)

    first_fuel_id = 2
    fuel_ids: list[int] = []
    for index in range(segment_count):
        part_id = first_fuel_id + index
        position_y = base_y - (spacing * index)
        segment_shape = segment_shape_profile[index]
        _fuel_stage(
            parts,
            params,
            part_id,
            position_y,
            segment_capacity,
            top_scale=segment_shape["top"],
            bottom_scale=segment_shape["bottom"],
            deform_x=segment_shape["deform_x"],
        )
        fuel_ids.append(part_id)

    engine_id = first_fuel_id + segment_count
    engine_pos_y = (base_y - (spacing * (segment_count - 1))) - 0.12
    _engine(parts, profile, params, engine_id, engine_pos_y)

    connections = ET.SubElement(assembly, "Connections")
    if int(params["stages"]) > 1:
        _stage_separator(parts)
        first = ET.SubElement(connections, "Connection", partA="1", partB="0", attachPointsA="2", attachPointsB="2")
        ET.SubElement(first, "BodyJoint", body="2", connectedBody="1", breakTorque="1E+07", breakForce="0", jointType="Normal", position="0,0.8050811,0", connectedPosition="0,-0.7074974,0", axis="0,0,1", secondaryAxis="0,1,0")
        ET.SubElement(connections, "Connection", partA=str(fuel_ids[0]), partB="1", attachPointsA="2,4", attachPointsB="1,0")
    else:
        ET.SubElement(connections, "Connection", partA=str(fuel_ids[0]), partB="0", attachPointsA="2,4", attachPointsB="2,1")

    for index in range(1, len(fuel_ids)):
        ET.SubElement(
            connections,
            "Connection",
            partA=str(fuel_ids[index]),
            partB=str(fuel_ids[index - 1]),
            attachPointsA="2,4",
            attachPointsB="1,0",
        )

    ET.SubElement(connections, "Connection", partA=str(engine_id), partB=str(fuel_ids[-1]), attachPointsA="0", attachPointsB="1")

    ET.SubElement(assembly, "Collisions")
    bodies = ET.SubElement(assembly, "Bodies")
    if int(params["stages"]) > 1:
        ET.SubElement(bodies, "Body", id="1", partIds="0", mass=_fmt(10.95 * float(params["mass_scale"])), position="0,0.75,0", rotation="0,0,0", centerOfMass="0,0,0")
        staged_part_ids = ",".join(["1", *[str(part_id) for part_id in fuel_ids], str(engine_id)])
        mass = (18.5 + 2.8 * max(0, segment_count - 1)) * float(params["mass_scale"])
        ET.SubElement(bodies, "Body", id="2", partIds=staged_part_ids, mass=_fmt(mass), position="0,-0.45,0", rotation="0,0,0", centerOfMass="0,0,0")
    else:
        part_ids = ",".join(["0", *[str(part_id) for part_id in fuel_ids], str(engine_id)])
        mass = (24.0 + 3.4 * max(0, segment_count - 1)) * float(params["mass_scale"])
        ET.SubElement(bodies, "Body", id="1", partIds=part_ids, mass=_fmt(mass), position="0,-0.1,0", rotation="0,0,0", centerOfMass="0,0,0")


def _assembly_battery_launcher(root: ET.Element, profile: CraftProfile, params: dict[str, int | float | str]) -> None:
    assembly = ET.SubElement(root, "Assembly")
    parts = ET.SubElement(assembly, "Parts")
    size_mul = float(params.get("size_multiplier", 1.0) or 1.0)

    def _scaled_pos(x: float, y: float, z: float) -> str:
        return f"{_fmt(x * size_mul)},{_fmt(y * size_mul)},{_fmt(z * size_mul)}"

    def _scaled_pair(value: float) -> str:
        scaled = max(0.2, value * size_mul)
        return f"{_fmt(scaled)},{_fmt(scaled)}"

    def _add_real_detail_parts(start_id: int, anchor_part_id: int, count: int) -> list[int]:
        detail_ids: list[int] = []
        grid_x = 18
        grid_z = 18
        per_layer = grid_x * grid_z
        base_scale = max(0.06, 0.09 * size_mul)
        x_step = 0.13 * size_mul
        z_step = 0.13 * size_mul
        y_step = 0.045 * size_mul
        y_base = -0.05 * size_mul
        z_center = -0.35 * size_mul
        for index in range(count):
            layer = index // per_layer
            local = index % per_layer
            ix = local % grid_x
            iz = local // grid_x

            x = (ix - (grid_x - 1) / 2) * x_step
            z = z_center + (iz - (grid_z - 1) / 2) * z_step
            y = y_base + (layer * y_step)

            # Stagger every odd layer slightly so the mesh looks more organic.
            if layer % 2 == 1:
                x += 0.5 * x_step
                z += 0.5 * z_step

            detail_id = start_id + index
            part = ET.SubElement(
                parts,
                "Part",
                id=str(detail_id),
                partType="Fuselage1",
                position=f"{_fmt(x)},{_fmt(y)},{_fmt(z)}",
                rotation="90,0,0",
                name="Internal Detail Cell",
                commandPodId="0",
                materials="18,4,4,0,0",
                texture="Fuselage10",
                textureTiling="2.6,2.6",
            )
            ET.SubElement(part, "Drag", drag="0.45,0.45,0,0.04,0.45,0.45", area="0.6,0.6,0,0.04,0.6,0.6")
            ET.SubElement(part, "Config", heatShieldScale="0")
            ET.SubElement(
                part,
                "Fuselage",
                bottomScale=f"{_fmt(base_scale)},{_fmt(base_scale)}",
                topScale=f"{_fmt(base_scale)},{_fmt(base_scale)}",
                deadWeightPercentage="0",
                deformations="0,0,0",
                depthCurve="0",
                fuelPercentage="0",
                offset=f"0,{_fmt(0.08 * size_mul)},0",
                version="2",
            )
            ET.SubElement(part, "FuelTank", capacity="8", fuel="8", fuelType="Monopropellant", subPriority="20")
            ET.SubElement(
                connections,
                "Connection",
                partA=str(detail_id),
                partB=str(anchor_part_id),
                attachPointsA="2,4",
                attachPointsB="1,0",
            )
            detail_ids.append(detail_id)
        return detail_ids

    # Command module on rear platform.
    _command_pod(parts, profile, params)
    if len(parts):
        parts[0].set("position", _scaled_pos(0.0, -0.22, -0.62))

    pid = 2

    # Wide ground deck like launcher carrier platform.
    deck_id = pid
    deck = ET.SubElement(
        parts,
        "Part",
        id=str(deck_id),
        partType="Fuselage1",
        position=_scaled_pos(0.48, -0.08, -0.48),
        rotation="90,0,0",
        name="Base Deck",
        commandPodId="0",
        materials="18,4,4,0,0",
        texture="Fuselage10",
        textureTiling="7.4,3.4",
    )
    ET.SubElement(deck, "Drag", drag="1.2,1.2,0,0.12,1.2,1.2", area="1.9,1.9,0,0.12,1.9,1.9")
    ET.SubElement(deck, "Config", heatShieldScale="0")
    ET.SubElement(
        deck,
        "Fuselage",
        bottomScale=_scaled_pair(2.72),
        topScale=_scaled_pair(2.72),
        deadWeightPercentage="0",
        deformations="0,0,0",
        depthCurve="0",
        fuelPercentage="0",
        offset=f"0,{_fmt(0.22 * size_mul)},0",
        version="2",
    )
    ET.SubElement(deck, "FuelTank", capacity="520", fuel="520", fuelType="Monopropellant", subPriority="20")
    pid += 1

    # Base chassis pieces.
    platform_ids: list[int] = []
    base_positions = [
        (-0.62, 0.10, 0.25),
        (0.62, 0.10, 0.25),
        (-0.62, 0.10, -0.55),
        (0.62, 0.10, -0.55),
        (0.0, 0.10, -0.15),
    ]
    for x, y, z in base_positions:
        part = ET.SubElement(
            parts,
            "Part",
            id=str(pid),
            partType="Fuselage1",
            position=_scaled_pos(x, y, z),
            rotation="90,0,0",
            name="Platform Segment",
            commandPodId="0",
            materials="18,4,4,0,0",
            texture="Fuselage10",
            textureTiling="5.2,2.6",
        )
        ET.SubElement(part, "Drag", drag="1.1,1.1,0,0.11,1.1,1.1", area="1.6,1.6,0,0.11,1.6,1.6")
        ET.SubElement(part, "Config", heatShieldScale="0")
        ET.SubElement(
            part,
            "Fuselage",
            bottomScale=_scaled_pair(1.28),
            topScale=_scaled_pair(1.28),
            deadWeightPercentage="0",
            deformations="0,0,0",
            depthCurve="0",
            fuelPercentage="0",
            offset=f"0,{_fmt(0.42 * size_mul)},0",
            version="2",
        )
        ET.SubElement(part, "FuelTank", capacity="350", fuel="350", fuelType="Monopropellant", subPriority="20")
        platform_ids.append(pid)
        pid += 1

    # Keep thin hidden masts (used as structure anchors) near radar side.
    tower_positions = [(0.72, 0.22, -0.86), (0.86, 0.22, -1.06)]
    tower_ids: list[int] = []
    for x, y, z in tower_positions:
        part = ET.SubElement(
            parts,
            "Part",
            id=str(pid),
            partType="Fuselage1",
            position=_scaled_pos(x, y, z),
            rotation="0,0,0",
            name="Radar Mast",
            commandPodId="0",
            materials="18,4,4,0,0",
            texture="Fuselage10",
            textureTiling="2.4,3.6",
        )
        ET.SubElement(part, "Drag", drag="0.9,0.9,0,0.08,0.9,0.9", area="1.2,1.2,0,0.08,1.2,1.2")
        ET.SubElement(part, "Config", heatShieldScale="0")
        ET.SubElement(
            part,
            "Fuselage",
            bottomScale=_scaled_pair(0.28),
            topScale=_scaled_pair(0.24),
            deadWeightPercentage="0",
            deformations="0.06,0,0",
            depthCurve="0",
            fuelPercentage="0",
            offset=f"0,{_fmt(0.28 * size_mul)},0",
            version="2",
        )
        ET.SubElement(part, "FuelTank", capacity="220", fuel="220", fuelType="Monopropellant", subPriority="20")
        tower_ids.append(pid)
        pid += 1

    # Radar/electronics cabinet blocks.
    cabinet_ids: list[int] = []
    cabinet_specs = [
        (1.04, 0.24, -0.58, 1.32, 1.18, 0.42),
        (1.02, 0.58, -1.04, 1.48, 1.32, 0.42),
    ]
    for x, y, z, base_scale_value, top_scale_value, offset_y in cabinet_specs:
        part = ET.SubElement(
            parts,
            "Part",
            id=str(pid),
            partType="Fuselage1",
            position=_scaled_pos(x, y, z),
            rotation="90,0,0",
            name="Radar Cabinet",
            commandPodId="0",
            materials="18,4,4,0,0",
            texture="Fuselage10",
            textureTiling="3.4,2.0",
        )
        ET.SubElement(part, "Drag", drag="0.95,0.95,0,0.08,0.95,0.95", area="1.5,1.5,0,0.08,1.5,1.5")
        ET.SubElement(part, "Config", heatShieldScale="0")
        ET.SubElement(
            part,
            "Fuselage",
            bottomScale=_scaled_pair(base_scale_value),
            topScale=_scaled_pair(top_scale_value),
            deadWeightPercentage="0",
            deformations="0,0,0",
            depthCurve="0",
            fuelPercentage="0",
            offset=f"0,{_fmt(offset_y * size_mul)},0",
            version="2",
        )
        ET.SubElement(part, "FuelTank", capacity="260", fuel="260", fuelType="Monopropellant", subPriority="20")
        cabinet_ids.append(pid)
        pid += 1

    # Launcher side rails.
    rail_ids: list[int] = []
    rail_specs = [(-0.58, 0.48, 0.12), (0.58, 0.48, 0.12)]
    for x, y, z in rail_specs:
        part = ET.SubElement(
            parts,
            "Part",
            id=str(pid),
            partType="Fuselage1",
            position=_scaled_pos(x, y, z),
            rotation="0,0,0",
            name="Launcher Rail",
            commandPodId="0",
            materials="18,4,4,0,0",
            texture="Fuselage10",
            textureTiling="3.2,4.6",
        )
        ET.SubElement(part, "Drag", drag="0.6,0.6,0,0.06,0.6,0.6", area="0.8,0.8,0,0.06,0.8,0.8")
        ET.SubElement(part, "Config", heatShieldScale="0")
        ET.SubElement(
            part,
            "Fuselage",
            bottomScale=_scaled_pair(0.34),
            topScale=_scaled_pair(0.3),
            deadWeightPercentage="0",
            deformations="0,0,0",
            depthCurve="0",
            fuelPercentage="0",
            offset=f"0,{_fmt(1.56 * size_mul)},0",
            version="2",
        )
        ET.SubElement(part, "FuelTank", capacity="80", fuel="80", fuelType="Monopropellant", subPriority="20")
        rail_ids.append(pid)
        pid += 1

    # Launch tubes in dense 3x3 pack to match THAAD-style battery silhouette.
    tube_ids: list[int] = []
    tube_positions: list[tuple[float, float, float]] = []
    x_slots = (-0.44, 0.0, 0.44)
    z_slots = (0.98, 0.54, 0.10)
    y_slots = (0.56, 0.56, 0.56)
    for z, y in zip(z_slots, y_slots):
        for x in x_slots:
            tube_positions.append((x, y, z))
    for x, y, z in tube_positions:
        part = ET.SubElement(
            parts,
            "Part",
            id=str(pid),
            partType="Fuselage1",
            position=_scaled_pos(x, y, z),
            rotation="90,0,0",
            name="Launch Tube",
            commandPodId="0",
            materials="18,4,4,0,0",
            texture="Fuselage10",
            textureTiling="7.8,2.2",
        )
        ET.SubElement(part, "Drag", drag="0.8,0.8,0,0.08,0.8,0.8", area="1.0,1.0,0,0.08,1.0,1.0")
        ET.SubElement(part, "Config", heatShieldScale="0")
        ET.SubElement(
            part,
            "Fuselage",
            bottomScale=_scaled_pair(0.42),
            topScale=_scaled_pair(0.40),
            deadWeightPercentage="0",
            deformations="0,0,0",
            depthCurve="0",
            fuelPercentage="0",
            offset=f"0,{_fmt(1.68 * size_mul)},0",
            version="2",
        )
        ET.SubElement(part, "FuelTank", capacity="280", fuel="280", fuelType="Monopropellant", subPriority="20")
        tube_ids.append(pid)
        pid += 1

    # Under-rack support legs.
    support_ids: list[int] = []
    support_positions = [(-0.82, -0.22, -0.95), (0.82, -0.22, -0.95), (-0.82, -0.22, 0.55), (0.82, -0.22, 0.55)]
    for x, y, z in support_positions:
        part = ET.SubElement(
            parts,
            "Part",
            id=str(pid),
            partType="Fuselage1",
            position=_scaled_pos(x, y, z),
            rotation="0,0,0",
            name="Support Leg",
            commandPodId="0",
            materials="18,4,4,0,0",
            texture="Fuselage10",
            textureTiling="1.8,3.4",
        )
        ET.SubElement(part, "Drag", drag="0.3,0.3,0,0.03,0.3,0.3", area="0.35,0.35,0,0.03,0.35,0.35")
        ET.SubElement(part, "Config", heatShieldScale="0")
        ET.SubElement(
            part,
            "Fuselage",
            bottomScale=_scaled_pair(0.24),
            topScale=_scaled_pair(0.2),
            deadWeightPercentage="0",
            deformations="0,0,0",
            depthCurve="0",
            fuelPercentage="0",
            offset=f"0,{_fmt(0.24 * size_mul)},0",
            version="2",
        )
        ET.SubElement(part, "FuelTank", capacity="45", fuel="45", fuelType="Monopropellant", subPriority="20")
        support_ids.append(pid)
        pid += 1

    # Main propulsion for mobility / launch behavior.
    _engine(parts, profile, params, part_id=pid, position_y=-0.24 * size_mul)
    engine_id = pid

    connections = ET.SubElement(assembly, "Connections")
    for base_id in platform_ids:
        ET.SubElement(connections, "Connection", partA=str(base_id), partB="0", attachPointsA="2,4", attachPointsB="2,1")

    for tower_id in tower_ids:
        ET.SubElement(connections, "Connection", partA=str(tower_id), partB=str(platform_ids[-1]), attachPointsA="2,4", attachPointsB="1,0")

    for cabinet_id in cabinet_ids:
        ET.SubElement(connections, "Connection", partA=str(cabinet_id), partB=str(platform_ids[-1]), attachPointsA="2,4", attachPointsB="1,0")

    ET.SubElement(connections, "Connection", partA=str(deck_id), partB="0", attachPointsA="2,4", attachPointsB="2,1")

    for rail_id in rail_ids:
        ET.SubElement(connections, "Connection", partA=str(rail_id), partB=str(platform_ids[0]), attachPointsA="2,4", attachPointsB="1,0")

    for tube_id in tube_ids:
        ET.SubElement(connections, "Connection", partA=str(tube_id), partB=str(platform_ids[0]), attachPointsA="2,4", attachPointsB="1,0")

    for support_id in support_ids:
        ET.SubElement(connections, "Connection", partA=str(support_id), partB=str(platform_ids[2]), attachPointsA="2,4", attachPointsB="1,0")

    ET.SubElement(connections, "Connection", partA=str(engine_id), partB=str(platform_ids[2]), attachPointsA="0", attachPointsB="1")

    detail_ids: list[int] = []
    min_output_lines = int(params.get("min_output_lines", 0) or 0)
    real_output_lines = bool(params.get("real_output_lines", False))
    if real_output_lines and min_output_lines > 0:
        base_line_estimate = 220
        lines_per_detail = 7
        needed = max(0, (min_output_lines - base_line_estimate + (lines_per_detail - 1)) // lines_per_detail)
        needed += 120
        needed = min(5000, needed)
        detail_ids = _add_real_detail_parts(start_id=engine_id + 1, anchor_part_id=platform_ids[2], count=needed)

    ET.SubElement(assembly, "Collisions")
    bodies = ET.SubElement(assembly, "Bodies")
    all_ids = [
        "0",
        *[str(part_id) for part_id in platform_ids],
        str(deck_id),
        *[str(part_id) for part_id in tower_ids],
        *[str(part_id) for part_id in cabinet_ids],
        *[str(part_id) for part_id in rail_ids],
        *[str(part_id) for part_id in tube_ids],
        *[str(part_id) for part_id in support_ids],
        str(engine_id),
        *[str(part_id) for part_id in detail_ids],
    ]
    ET.SubElement(
        bodies,
        "Body",
        id="1",
        partIds=",".join(all_ids),
        mass=_fmt(34.0 * float(params["mass_scale"])),
        position="0,0.65,-0.2",
        rotation="0,0,0",
        centerOfMass="0,0,0",
    )


def generate_craft_xml(params: dict[str, int | float | str]) -> str:
    if bool(params.get("prefer_template", False)):
        template_xml = load_template_xml(params)
        if template_xml:
            min_output_lines = int(params.get("min_output_lines", 0) or 0)
            if bool(params.get("real_output_lines", False)):
                return template_xml
            return _ensure_minimum_lines(template_xml, min_output_lines)

    profile = PROFILES[str(params["profile_id"])]
    price = str(max(25000, int(params["thrust"]) // 10 + int(params["fuel_capacity"]) // 2))
    craft_title = str(params.get("variant_name") or params["craft_name"])
    root = ET.Element(
        "Craft",
        name=craft_title,
        parent="",
        initialBoundsMin="-1.2,-2.4,-1.2",
        initialBoundsMax="1.2,1.4,1.2",
        removeInvalidParts="true",
        price=price,
        xmlVersion="14",
        activeCommandPod="0",
        localCenterOfMass="0,-0.2,0",
    )

    _assembly(root, profile, params)
    intercept_mach = params.get("target_intercept_mach")
    intercept_altitude = params.get("target_intercept_altitude_km")
    if intercept_mach or intercept_altitude:
        note_bits: list[str] = []
        if intercept_mach:
            note_bits.append(f"targetMach={intercept_mach}")
        if intercept_altitude:
            note_bits.append(f"targetAltitudeKm={intercept_altitude}")
        root.append(ET.Comment(" interceptor-profile " + " ".join(note_bits) + " "))
    _add_theme_section(root, profile.profile_id, params)

    xml_bytes = ET.tostring(root, encoding="utf-8")
    parsed = minidom.parseString(xml_bytes)
    xml_text = parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    min_output_lines = int(params.get("min_output_lines", 0) or 0)
    if bool(params.get("real_output_lines", False)):
        return xml_text
    return _ensure_minimum_lines(xml_text, min_output_lines)