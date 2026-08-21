import pytest

from src.diagram_ir import DiagramSpec, Node, Edge, Point, Region
from src.layout_engine import DiagramLayoutEngine, LayoutOptions, layout_diagram, layout_question_blocks
from src.layout_ir import Rect
from src.layout_validator import layout_report, validate_layout


def test_layout_result_has_canvas_and_content_items():
    spec = DiagramSpec(
        "block_diagram",
        title="Simple block",
        nodes=[
            Node("A", "block", "Input"),
            Node("B", "block", "Output"),
        ],
        edges=[Edge("A", "B", "signal", directed=True)],
    )
    result = layout_diagram(spec)
    assert result.width == 1000
    assert result.height == 650
    assert len(result.items) == 2
    assert result.validate() == []


def test_layout_is_deterministic():
    spec = DiagramSpec(
        "block_diagram",
        nodes=[
            Node("A", "block", "A"),
            Node("B", "block", "B"),
            Node("C", "block", "C"),
        ],
        edges=[Edge("A", "B"), Edge("B", "C")],
    )
    a = layout_diagram(spec).to_dict()
    b = layout_diagram(spec).to_dict()
    assert a == b


def test_layered_graph_has_connectors():
    spec = DiagramSpec(
        "signal_diagram",
        nodes=[
            Node("A", "block", "Input"),
            Node("B", "block", "Gain"),
            Node("C", "block", "Output"),
        ],
        edges=[
            Edge("A", "B", "signal", "x", True),
            Edge("B", "C", "signal", "y", True),
        ],
    )
    result = layout_diagram(spec)
    assert len(result.connectors) == 2
    assert result.connectors[0]["source"] == "A"
    assert result.connectors[1]["target"] == "C"


def test_cycle_layout_terminates_and_is_valid():
    spec = DiagramSpec(
        "control_system_diagram",
        nodes=[
            Node("A", "block", "A"),
            Node("B", "block", "B"),
            Node("C", "block", "C"),
        ],
        edges=[Edge("A", "B"), Edge("B", "C"), Edge("C", "A")],
    )
    result = layout_diagram(spec)
    assert len(result.items) == 3
    assert result.validate() == []


def test_explicit_node_positions_are_normalized_to_canvas():
    spec = DiagramSpec(
        "network_diagram",
        nodes=[
            Node("A", "vertex", "A", (-100, -100)),
            Node("B", "vertex", "B", (5000, 3000)),
        ],
        edges=[Edge("A", "B")],
    )
    result = layout_diagram(spec, width=800, height=500, margin=40)
    assert result.validate() == []
    for item in result.items:
        assert item.rect.within(800, 500, 40)


def test_node_boxes_do_not_overlap():
    spec = DiagramSpec(
        "block_diagram",
        nodes=[Node(f"N{i}", "block", str(i)) for i in range(10)],
        edges=[Edge(f"N{i}", f"N{i+1}") for i in range(9)],
    )
    result = layout_diagram(spec)
    assert result.overlaps(0.5) == []
    assert result.validate(0.5) == []


def test_geometry_points_fit_content_area():
    spec = DiagramSpec(
        "coordinate_geometry",
        coordinate_system="cartesian",
        points=[
            Point(-1000, -500, "A", "A"),
            Point(2500, 1800, "B", "B"),
            Point(5000, -1200, "C", "C"),
        ],
    )
    result = layout_diagram(spec, width=900, height=600, margin=45)
    assert result.validate() == []
    for item in result.items:
        assert item.rect.within(900, 600, 45)


def test_venn_regions_are_placed_without_overlap():
    spec = DiagramSpec(
        "venn_diagram",
        regions=[
            Region("A", "set", "A"),
            Region("B", "set", "B"),
        ],
    )
    result = layout_diagram(spec)
    assert len(result.items) == 2
    assert result.overlaps(0.5) == []


def test_component_layout_is_kept_inside_page():
    spec = DiagramSpec(
        "circuit_diagram",
        properties={
            "components": [
                {"type": "resistor", "label": "R1", "x1": 0, "y1": 0, "x2": 1000, "y2": 0},
                {"type": "capacitor", "label": "C1", "x1": 1000, "y1": 0, "x2": 1000, "y2": 1000},
            ]
        },
    )
    result = layout_diagram(spec, width=1000, height=650)
    assert result.validate() == []


def test_logic_gates_are_layout_items():
    spec = DiagramSpec(
        "logic_circuit",
        properties={
            "gates": [
                {"id": "G1", "type": "AND", "x": 100, "y": 100},
                {"id": "G2", "type": "OR", "x": 800, "y": 500},
            ]
        },
    )
    result = layout_diagram(spec)
    assert {x.kind for x in result.items} == {"gate"}
    assert result.validate() == []


def test_waveform_has_plot_layout_region():
    spec = DiagramSpec("waveform", properties={"waveform_type": "sine"})
    result = layout_diagram(spec)
    assert any(x.id == "waveform:plot" for x in result.items)
    assert result.validate() == []


def test_motor_has_machine_layout_region():
    result = layout_diagram(DiagramSpec("motor_diagram"))
    assert any(x.id == "motor:machine" for x in result.items)
    assert result.validate() == []


def test_phasor_vectors_create_layout_items():
    spec = DiagramSpec(
        "phasor_diagram",
        properties={
            "origin": (250, 430),
            "vectors": [
                {"label": "V", "magnitude": 200, "angle_deg": 30},
                {"label": "I", "magnitude": 150, "angle_deg": -20},
            ],
        },
    )
    result = layout_diagram(spec)
    assert len(result.items) == 2
    assert result.validate() == []


def test_question_blocks_stack_top_to_bottom():
    blocks = layout_question_blocks(
        [("q1", 800, 200), ("q2", 800, 300), ("q3", 800, 250)],
        width=900,
        height=900,
        margin=40,
        gap=20,
    )
    assert len(blocks) == 3
    assert blocks[0].rect.y < blocks[1].rect.y < blocks[2].rect.y


def test_question_block_width_is_clamped():
    blocks = layout_question_blocks(
        [("q1", 5000, 100)],
        width=900,
        height=500,
        margin=40,
    )
    assert blocks[0].rect.width == 820
    assert blocks[0].rect.within(900, 500, 40)


def test_layout_options_reject_invalid_canvas():
    with pytest.raises(ValueError):
        LayoutOptions(width=50, height=50, margin=30).validate()


def test_layout_options_reject_negative_gap():
    with pytest.raises(ValueError):
        LayoutOptions(gap=-1).validate()


def test_rect_intersection_uses_padding():
    a = Rect(0, 0, 10, 10)
    b = Rect(10.1, 0, 10, 10)
    assert not a.intersects(b)
    assert a.intersects(b, padding=1)


def test_layout_report_is_machine_readable():
    spec = DiagramSpec("block_diagram", nodes=[Node("A", "block", "A")])
    result = layout_diagram(spec)
    report = layout_report(result)
    assert report["valid"] is True
    assert report["items"] == 1
    assert report["overlaps"] == 0


def test_validator_returns_true_for_valid_layout():
    spec = DiagramSpec("network_diagram", nodes=[Node("A", "vertex", "A")])
    assert validate_layout(layout_diagram(spec))


def test_custom_canvas_size():
    result = layout_diagram(
        DiagramSpec("block_diagram", nodes=[Node("A", "block", "A")]),
        width=1200,
        height=800,
        margin=60,
    )
    assert result.width == 1200
    assert result.height == 800
    assert result.validate() == []


def test_layout_preserves_semantic_ids():
    spec = DiagramSpec(
        "network_diagram",
        nodes=[
            Node("source", "vertex", "S"),
            Node("sink", "vertex", "T"),
        ],
        edges=[Edge("source", "sink", "edge")],
    )
    result = layout_diagram(spec)
    assert {item.source for item in result.items} == {"source", "sink"}
    assert {c["source"] for c in result.connectors} == {"source"}


def test_layout_does_not_modify_input_spec():
    spec = DiagramSpec(
        "block_diagram",
        nodes=[
            Node("A", "block", "A"),
            Node("B", "block", "B"),
        ],
        edges=[Edge("A", "B")],
    )
    before = spec.to_dict()
    layout_diagram(spec)
    assert spec.to_dict() == before
