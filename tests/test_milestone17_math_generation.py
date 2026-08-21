import re

import pytest

from src.diagram_ir import Axis, DiagramSpec, Edge, Node, Point, Region, Series
from src.diagram_renderer import MathematicalDiagramRenderer, render_diagram
from src.mathematical_diagram_generator import MathematicalDiagramGenerator, generate_mathematical_diagram


@pytest.fixture
def renderer():
    return MathematicalDiagramRenderer()


def assert_svg(svg):
    assert svg.startswith('<svg ')
    assert svg.endswith('</svg>')
    assert '<title>' in svg
    assert '<rect' in svg
    assert 'NaN' not in svg
    assert 'undefined' not in svg


def test_coordinate_geometry_generates_svg(renderer):
    spec = DiagramSpec(
        "coordinate_geometry", title="Points",
        coordinate_system="cartesian",
        axes=[Axis("x", label="x", grid=True), Axis("y", label="y", grid=True)],
        points=[Point(1, 2, "A", "A"), Point(-2, 1, "B", "B")]
    )
    svg = renderer.render(spec)
    assert_svg(svg)
    assert 'Coordinate geometry' not in svg  # title is supplied as accessible title
    assert '>A<' in svg and '>B<' in svg
    assert '<circle' in svg


def test_graph_samples_function():
    spec = DiagramSpec(
        "graph", expressions=["y=x^2"],
        coordinate_system="cartesian",
        axes=[Axis("x", minimum=-3, maximum=3, grid=True),
              Axis("y", minimum=0, maximum=9, grid=True)]
    )
    svg = render_diagram(spec)
    assert_svg(svg)
    assert '<polyline' in svg


def test_function_plot_samples_trigonometry():
    spec = DiagramSpec(
        "function_plot", expressions=["sin(x)"],
        coordinate_system="cartesian",
        axes=[Axis("x", minimum=-4, maximum=4), Axis("y", minimum=-2, maximum=2)]
    )
    svg = render_diagram(spec)
    assert_svg(svg)
    assert '<polyline' in svg


def test_graph_discontinuity_does_not_emit_nan():
    spec = DiagramSpec(
        "graph", expressions=["1/x"],
        coordinate_system="cartesian",
        axes=[Axis("x", minimum=-3, maximum=3), Axis("y", minimum=-10, maximum=10)]
    )
    svg = render_diagram(spec)
    assert_svg(svg)


def test_geometric_triangle_generation():
    spec = DiagramSpec(
        "geometric_figure", points=[
            Point(0, 0, "A", "A"), Point(4, 0, "B", "B"), Point(2, 3, "C", "C")
        ],
        properties={"shape": "triangle", "closed": True}
    )
    svg = render_diagram(spec)
    assert_svg(svg)
    assert '<polyline' in svg
    assert '>C<' in svg


def test_geometric_circle_generation():
    spec = DiagramSpec(
        "geometric_figure",
        points=[Point(0, 0, "O", "O")],
        properties={"shape": "circle", "radius": 3}
    )
    svg = render_diagram(spec)
    assert_svg(svg)
    assert '<circle' in svg


def test_probability_tree_generation():
    spec = DiagramSpec(
        "probability_diagram",
        nodes=[Node("S", "root", "S", (100, 300)),
               Node("A", "event", "A", (350, 200)),
               Node("B", "event", "B", (350, 400))],
        edges=[Edge("S", "A", label="P(A)"), Edge("S", "B", label="P(B)")]
    )
    svg = render_diagram(spec)
    assert_svg(svg)
    assert 'P(A)' in svg and 'P(B)' in svg


def test_venn_generation():
    spec = DiagramSpec(
        "venn_diagram",
        regions=[
            Region("A", "set", "A", properties={"set": "A"}),
            Region("B", "set", "B", properties={"set": "B"})
        ]
    )
    svg = render_diagram(spec)
    assert_svg(svg)
    assert svg.count('<circle') >= 2
    assert '>A<' in svg and '>B<' in svg


def test_number_line_generation():
    spec = DiagramSpec(
        "number_line",
        points=[Point(-2, 0, "P1", "-2"), Point(3, 0, "P2", "3")]
    )
    svg = render_diagram(spec)
    assert_svg(svg)
    assert '>-2<' in svg and '>3<' in svg


def test_statistical_scatter_generation():
    spec = DiagramSpec(
        "statistical_plot",
        series=[Series(name="data", values=[1, 3, 2, 5], kind="scatter")],
        properties={"kind": "scatter"}
    )
    svg = render_diagram(spec)
    assert_svg(svg)
    assert '<circle' in svg


def test_statistical_histogram_generation():
    spec = DiagramSpec(
        "statistical_plot",
        series=[Series(name="data", values=[1, 1, 2, 2, 2, 3, 4], kind="histogram")],
        properties={"kind": "histogram"}
    )
    svg = render_diagram(spec)
    assert_svg(svg)
    assert '<rect' in svg


def test_statistical_box_generation():
    spec = DiagramSpec(
        "statistical_plot",
        series=[Series(name="data", values=[1, 2, 3, 4, 5], kind="box")],
        properties={"kind": "box"}
    )
    svg = render_diagram(spec)
    assert_svg(svg)
    assert 'width=' in svg


def test_generator_coordinate_question():
    r = MathematicalDiagramGenerator().generate(
        "Draw the coordinate plane with points A (1, 2) and B (-2, 3)."
    )
    assert r["diagram_type"] == "coordinate_geometry"
    assert_svg(r["svg"])
    assert len(r["spec"]["points"]) == 2


def test_generator_function_question():
    r = generate_mathematical_diagram("Plot f(x) = x^2 + 1.")
    assert r["diagram_type"] == "function_plot"
    assert r["spec"]["expressions"] == ["x^2 + 1"]
    assert '<polyline' in r["svg"]


def test_generator_triangle_question():
    r = generate_mathematical_diagram("Draw a triangle.")
    assert r["diagram_type"] == "geometric_figure"
    assert len(r["spec"]["points"]) == 3
    assert '<polyline' in r["svg"]


def test_generator_venn_question():
    r = generate_mathematical_diagram("Draw a Venn diagram for sets A and B.")
    assert r["diagram_type"] == "venn_diagram"
    assert '<circle' in r["svg"]


def test_generator_probability_question():
    r = generate_mathematical_diagram("Draw a probability tree.")
    assert r["diagram_type"] == "probability_diagram"
    assert len(r["spec"]["nodes"]) == 3
    assert '<line' in r["svg"]


def test_generator_number_line_question():
    r = generate_mathematical_diagram("Draw a number line marking -2, 0 and 4.")
    assert r["diagram_type"] == "number_line"
    assert len(r["spec"]["points"]) >= 3
    assert '<line' in r["svg"]


def test_generator_histogram_question():
    r = generate_mathematical_diagram("Plot a histogram for 1, 1, 2, 3, 3, 4.")
    assert r["diagram_type"] == "statistical_plot"
    assert r["spec"]["properties"]["kind"] == "histogram"
    assert '<rect' in r["svg"]


def test_m17_rejects_engineering_diagram():
    with pytest.raises(ValueError, match="M17"):
        generate_mathematical_diagram("Draw the transformer equivalent circuit.")


def test_m17_rejects_non_diagram_math():
    with pytest.raises(ValueError):
        generate_mathematical_diagram("Solve x^2 - 5x + 6 = 0.")


def test_save_output(tmp_path):
    path = tmp_path / "diagram.svg"
    r = generate_mathematical_diagram("Plot y = x^2.", output_path=path)
    assert path.exists()
    assert path.read_text(encoding="utf-8") == r["svg"]
    assert path.stat().st_size > 100


def test_deterministic_generation():
    q = "Plot y = x^2."
    a = generate_mathematical_diagram(q)["svg"]
    b = generate_mathematical_diagram(q)["svg"]
    assert a == b
