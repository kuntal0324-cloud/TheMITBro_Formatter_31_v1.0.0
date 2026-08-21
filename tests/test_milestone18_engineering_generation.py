import xml.etree.ElementTree as ET

import pytest

from src.diagram_ir import DiagramSpec, Node, Edge
from src.engineering_diagram_renderer import EngineeringDiagramRenderer, render_engineering_diagram
from src.engineering_diagram_generator import EngineeringDiagramGenerator, generate_engineering_diagram


ENGINEERING = [
    "circuit_diagram", "block_diagram", "signal_diagram", "phasor_diagram",
    "vector_diagram", "transformer_equivalent_circuit", "motor_diagram",
    "control_system_diagram", "logic_circuit", "waveform", "network_diagram",
]


def assert_svg(svg):
    assert svg.startswith("<svg ")
    assert svg.endswith("</svg>")
    assert "<title>" in svg
    assert '<rect x="0" y="0" width="100%"' in svg
    assert "NaN" not in svg
    assert "undefined" not in svg
    ET.fromstring(svg)


def test_all_engineering_families_have_renderer():
    r = EngineeringDiagramRenderer()
    assert r.SUPPORTED == set(ENGINEERING)
    for typ in ENGINEERING:
        spec = DiagramSpec(typ, title=typ)
        if typ in {"block_diagram", "signal_diagram", "control_system_diagram", "network_diagram"}:
            spec.nodes=[Node("A","block","A",(200,300)), Node("B","block","B",(500,300))]
            spec.edges=[Edge("A","B","signal","x",True)]
        svg = r.render(spec)
        assert_svg(svg)


def test_circuit_structured_generation():
    data = {
        "diagram_type": "circuit_diagram",
        "properties": {"components": [
            {"type":"voltage_source","label":"Vs","x1":120,"y1":350,"x2":120,"y2":230},
            {"type":"resistor","label":"R1","x1":120,"y1":230,"x2":360,"y2":230},
            {"type":"capacitor","label":"C1","x1":360,"y1":230,"x2":360,"y2":430},
            {"type":"wire","x1":360,"y1":430,"x2":120,"y2":430},
            {"type":"wire","x1":120,"y1":430,"x2":120,"y2":350},
        ]}
    }
    r=generate_engineering_diagram("Draw circuit", data)
    assert_svg(r["svg"])
    assert "R1" in r["svg"] and "C1" in r["svg"]


@pytest.mark.parametrize("question,typ", [
    ("Draw a circuit diagram with resistor and capacitor.", "circuit_diagram"),
    ("Draw a block diagram of input controller plant output.", "block_diagram"),
    ("Draw a signal-flow diagram.", "signal_diagram"),
    ("Draw a phasor diagram V=10∠30°.", "phasor_diagram"),
    ("Draw a vector diagram.", "vector_diagram"),
    ("Draw the transformer equivalent circuit with R1 and X1.", "transformer_equivalent_circuit"),
    ("Draw the induction motor showing stator and rotor.", "motor_diagram"),
    ("Draw the closed-loop control system with feedback.", "control_system_diagram"),
    ("Draw the NAND logic circuit.", "logic_circuit"),
    ("Plot a square wave waveform.", "waveform"),
    ("Draw a network diagram.", "network_diagram"),
])
def test_natural_language_families(question, typ):
    r=generate_engineering_diagram(question)
    assert r["diagram_type"] == typ
    assert_svg(r["svg"])


def test_circuit_has_expected_symbols():
    r=generate_engineering_diagram("Draw a circuit diagram with resistor capacitor inductor.")
    assert "<polyline" in r["svg"]  # resistor/inductor bodies
    assert r["svg"].count("<line") >= 4


def test_control_system_has_feedback_edges():
    r=generate_engineering_diagram("Draw the closed-loop control system with feedback.")
    assert "Closed-loop control system" in r["svg"]
    assert "−" in r["svg"]
    assert r["svg"].count("<line") >= 4


def test_logic_gate_variants():
    for gate in ["AND","OR","NOT","NAND","NOR","XOR","XNOR"]:
        r=generate_engineering_diagram(f"Draw a {gate} logic circuit.")
        assert gate in r["svg"]
        assert_svg(r["svg"])


def test_waveform_variants():
    for kind in ["sine","square","triangle","sawtooth"]:
        r=generate_engineering_diagram(f"Plot a {kind} waveform amplitude=2 frequency=3.")
        assert r["spec"]["properties"]["waveform_type"] == kind
        assert "<polyline" in r["svg"]


def test_phasor_parser():
    r=generate_engineering_diagram("Draw phasors V=10∠30° and I=5∠-20°.")
    assert len(r["spec"]["properties"]["vectors"]) == 2
    assert "V" in r["svg"] and "I" in r["svg"]


def test_vector_renderer_uses_arrows():
    r=generate_engineering_diagram("Draw a vector diagram.")
    assert "<polygon" in r["svg"]


def test_network_edges_are_rendered():
    data={
        "diagram_type":"network_diagram",
        "nodes":[{"id":"A","kind":"vertex","label":"A","position":[200,300]},
                 {"id":"B","kind":"vertex","label":"B","position":[500,300]}],
        "edges":[{"source":"A","target":"B","kind":"edge"}],
    }
    r=generate_engineering_diagram("Draw network",data)
    assert_svg(r["svg"])
    assert ">A<" in r["svg"] and ">B<" in r["svg"]


def test_transformer_contains_core_equivalent_components():
    r=generate_engineering_diagram("Draw the transformer equivalent circuit.")
    for label in ["R1","X1","R2'","X2'","Rc","Xm"]:
        assert label in r["svg"] or label.replace("'", "&#x27;") in r["svg"]


def test_motor_contains_stator_rotor_and_speed():
    r=generate_engineering_diagram("Draw the induction motor showing stator and rotor.")
    assert "Rotor" in r["svg"] and "Stator" in r["svg"] and "ωm" in r["svg"]
    assert r["svg"].count("<circle") >= 2


def test_engineering_only_rejects_math():
    with pytest.raises(ValueError):
        generate_engineering_diagram("Solve x^2 - 5x + 6 = 0.")


def test_engineering_only_rejects_math_diagram():
    with pytest.raises(ValueError):
        generate_engineering_diagram("Draw a coordinate plane with A (1,2).")


def test_structured_math_type_rejected():
    with pytest.raises(ValueError):
        generate_engineering_diagram(
            "Draw circuit",
            {"diagram_type":"function_plot","coordinate_system":"cartesian"}
        )


def test_invalid_structured_engineering_spec_rejected():
    with pytest.raises(ValueError):
        generate_engineering_diagram(
            "Draw network",
            {"diagram_type":"network_diagram",
             "nodes":[{"id":"A","kind":"vertex"}],
             "edges":[{"source":"A","target":"MISSING"}]}
        )


def test_deterministic_generation():
    q="Draw the transformer equivalent circuit."
    a=generate_engineering_diagram(q)["svg"]
    b=generate_engineering_diagram(q)["svg"]
    assert a == b


def test_output_file(tmp_path):
    p=tmp_path/"engineering.svg"
    r=generate_engineering_diagram("Draw a NAND logic circuit.", output_path=p)
    assert p.exists()
    assert p.read_text(encoding="utf-8")==r["svg"]
    assert p.stat().st_size > 200


def test_renderer_rejects_math():
    with pytest.raises(ValueError, match="M18"):
        render_engineering_diagram(DiagramSpec("graph", coordinate_system="cartesian"))


def test_svg_accessibility():
    r=generate_engineering_diagram("Draw a block diagram.")
    assert 'role="img"' in r["svg"]
    assert "<desc>" in r["svg"]


def test_no_external_image_backend():
    # Renderer must remain standalone SVG and not depend on matplotlib/GUI output.
    r=generate_engineering_diagram("Plot a square wave waveform.")
    assert "<svg " in r["svg"]
    assert "matplotlib" not in r["svg"].lower()
