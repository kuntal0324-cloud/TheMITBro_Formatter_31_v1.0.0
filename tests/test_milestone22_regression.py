import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from src.diagram_detector import detect_diagram_type
from src.mathematical_diagram_generator import MathematicalDiagramGenerator
from src.engineering_diagram_generator import EngineeringDiagramGenerator
from src.layout_engine import DiagramLayoutEngine
from src.layout_ir import LayoutOptions
from src.diagram_ir import DiagramSpec, Point, Node, Edge, Axis, Series
from src.question_paper_ir import PaperSpec, QuestionSpec
from src.question_paper_renderer import QuestionPaperRenderer
from src.question_paper_validator import validate_rendered_paper
from src.pdf_production import render_paper_pdf
from src.html_production import render_paper_html


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "input" / "milestone22_regression_corpus.json"


def load_corpus():
    return json.loads(CORPUS.read_text(encoding="utf-8"))


def test_corpus_is_complete_and_balanced():
    data = load_corpus()
    assert data["version"] == "22.0"
    assert data["case_count"] == len(data["cases"]) == 76
    counts = {}
    for case in data["cases"]:
        counts[case["family"]] = counts.get(case["family"], 0) + 1
        assert case["id"] and case["prompt"]
    assert len(counts) == 19
    assert min(counts.values()) >= 4
    assert sum(counts.values()) == 76


@pytest.mark.parametrize("case", load_corpus()["cases"], ids=lambda c: c["id"])
def test_detection_corpus(case):
    detection = detect_diagram_type(case["prompt"])
    assert detection is not None
    assert detection.diagram_type == case["family"]
    assert 0.75 <= detection.confidence <= 0.99


@pytest.mark.parametrize(
    "case",
    load_corpus()["cases"][::2],
    ids=lambda c: c["id"],
)
def test_generation_corpus_produces_valid_svg(case):
    family = case["family"]
    if family in {
        "coordinate_geometry", "graph", "geometric_figure", "probability_diagram",
        "venn_diagram", "function_plot", "number_line", "statistical_plot"
    }:
        result = MathematicalDiagramGenerator().generate(case["prompt"])
    else:
        result = EngineeringDiagramGenerator().generate(case["prompt"])

    assert result["diagram_type"] == family
    svg = result["svg"]
    assert svg.startswith("<svg ")
    assert "</svg>" in svg
    assert "NaN" not in svg
    assert "undefined" not in svg
    ET.fromstring(svg)


@pytest.mark.parametrize(
    "case",
    load_corpus()["cases"][1::2],
    ids=lambda c: c["id"],
)
def test_generation_is_deterministic(case):
    family = case["family"]
    generator = (
        MathematicalDiagramGenerator()
        if family in {
            "coordinate_geometry", "graph", "geometric_figure", "probability_diagram",
            "venn_diagram", "function_plot", "number_line", "statistical_plot"
        }
        else EngineeringDiagramGenerator()
    )
    a = generator.generate(case["prompt"])
    b = generator.generate(case["prompt"])
    assert a["diagram_type"] == b["diagram_type"]
    assert a["svg"] == b["svg"]


def test_math_engine_rejects_engineering_request():
    with pytest.raises(ValueError):
        MathematicalDiagramGenerator().generate("Draw an induction motor diagram.")


def test_engineering_engine_rejects_math_request():
    with pytest.raises(ValueError):
        EngineeringDiagramGenerator().generate("Draw a coordinate geometry diagram.")


@pytest.mark.parametrize(
    "diagram_type",
    [
        "coordinate_geometry", "graph", "geometric_figure", "probability_diagram",
        "venn_diagram", "function_plot", "number_line", "statistical_plot",
        "circuit_diagram", "block_diagram", "signal_diagram", "phasor_diagram",
        "vector_diagram", "transformer_equivalent_circuit", "motor_diagram",
        "control_system_diagram", "logic_circuit", "waveform", "network_diagram",
    ],
)
def test_all_19_families_have_m19_layout_samples(diagram_type):
    path = ROOT / "output" / "milestone19_layout_samples"
    matches = list(path.glob("*.json"))
    assert any(
        json.loads(p.read_text(encoding="utf-8"))["diagram_type"] == diagram_type
        for p in matches
    )


def test_layout_is_deterministic():
    spec = DiagramSpec(
        "coordinate_geometry",
        title="Regression",
        coordinate_system="cartesian",
        points=[
            Point(0, 0, id="A", label="A"),
            Point(3, 4, id="B", label="B"),
        ],
        axes=[Axis("x", label="x"), Axis("y", label="y")],
    )
    engine = DiagramLayoutEngine(LayoutOptions(width=900, height=600, margin=48))
    a = engine.layout(spec).to_dict()
    b = engine.layout(spec).to_dict()
    assert a == b
    assert a["metadata"]["deterministic"] is True


def test_layout_handles_engineering_nodes_and_edges():
    spec = DiagramSpec(
        "block_diagram",
        nodes=[
            Node("in", "block", "Input", (150, 300)),
            Node("out", "block", "Output", (550, 300)),
        ],
        edges=[Edge("in", "out", "signal", "u(t)")],
    )
    result = DiagramLayoutEngine().layout(spec)
    assert result.items
    assert result.connectors
    assert result.validate() == []


def test_question_paper_full_chain_remains_valid():
    paper = PaperSpec(
        title="M22 Regression Paper",
        subject="Engineering Mathematics",
        exam="TheMITbro",
        duration_minutes=60,
        total_marks=10,
        instructions=["Answer all questions."],
        questions=[
            QuestionSpec("q1", "Find the determinant of a 2x2 matrix.", number=1, marks=5),
            QuestionSpec("q2", "Draw the coordinate geometry diagram for A(0,0) and B(3,4).", number=2, marks=5),
        ],
    )
    rendered = QuestionPaperRenderer().render(paper)
    report = validate_rendered_paper(rendered)
    assert report["valid"]
    assert rendered.pages


def test_pdf_and_html_regression_outputs(tmp_path):
    paper = PaperSpec(
        title="M22 Production Regression",
        subject="Engineering",
        exam="TheMITbro",
        duration_minutes=30,
        total_marks=5,
        questions=[
            QuestionSpec("q1", "For z=2+3i, find |z|.", number=1, marks=5),
        ],
    )
    pdf = tmp_path / "paper.pdf"
    html = tmp_path / "paper.html"
    render_paper_pdf(paper, pdf)
    render_paper_html(paper, html)

    pdf_bytes = pdf.read_bytes()
    html_text = html.read_text(encoding="utf-8")

    assert pdf_bytes.startswith(b"%PDF-")
    assert b"%%EOF" in pdf_bytes
    assert len(pdf_bytes) > 1000
    assert html_text.startswith("<!doctype html>")
    assert "<svg " in html_text
    assert "M21" in html_text
    assert "<script src=" not in html_text


def test_existing_m17_m18_samples_are_valid_svg():
    for family_dir in ("milestone17_samples", "milestone18_samples"):
        directory = ROOT / "output" / family_dir
        files = sorted(directory.glob("*.svg"))
        assert files
        for path in files:
            text = path.read_text(encoding="utf-8")
            assert "NaN" not in text
            assert "undefined" not in text
            ET.fromstring(text)


def test_existing_m21_artifacts_are_present():
    pdf = ROOT / "output/milestone21_samples/representative.pdf"
    html = ROOT / "output/milestone21_samples/representative.html"
    assert pdf.is_file() and pdf.stat().st_size > 1000
    assert html.is_file() and html.stat().st_size > 1000
    assert pdf.read_bytes().startswith(b"%PDF-")
    assert b"%%EOF" in pdf.read_bytes()
    text = html.read_text(encoding="utf-8")
    assert "<svg" in text.lower()
    assert 'id="themitbro-manifest"' in text
