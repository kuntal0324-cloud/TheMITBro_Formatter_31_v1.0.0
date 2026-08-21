import copy
import xml.etree.ElementTree as ET

import pytest

from src.diagram_ir import DiagramSpec, Node, Edge, Point, Axis
from src.question_paper_ir import PaperSpec, QuestionSpec
from src.question_paper_renderer import PaperRenderOptions, QuestionPaperRenderer, render_question_paper
from src.question_paper_validator import validate_question_paper, validate_rendered_paper


def simple_paper():
    return PaperSpec(
        title="GATE EE Practice Paper",
        subject="Electrical Engineering",
        exam="TheMITbro",
        duration_minutes=60,
        total_marks=10,
        instructions=["Answer all questions.", "Use standard mathematical notation."],
        questions=[
            QuestionSpec("q1", "Find the value of $2+3$.", number=1, marks=2),
            QuestionSpec("q2", "For $z=2+3i$, find $|z|$.", number=2, marks=3,
                          options=["$5$", "$\\sqrt{13}$", "$13$", "$1$"]),
            QuestionSpec("q3", "Draw the coordinate geometry figure.", number=3, marks=5,
                          diagrams=[DiagramSpec("coordinate_geometry", title="Points",
                              coordinate_system="cartesian",
                              points=[Point(0,0,"A","A"), Point(2,3,"B","B")])]),
        ],
    )


def test_paper_spec_validation_and_total_marks():
    paper = PaperSpec("Test", [QuestionSpec("q1", "x=1", marks=2)])
    paper.ensure_valid()
    assert paper.resolved_total_marks() == 2


def test_renderer_is_deterministic():
    renderer = QuestionPaperRenderer()
    a = renderer.render(simple_paper()).to_dict()
    b = renderer.render(simple_paper()).to_dict()
    assert a == b


def test_renderer_produces_svg_page():
    result = QuestionPaperRenderer().render(simple_paper())
    assert len(result.pages) == 1
    svg = result.pages[0].svg
    assert svg.startswith("<svg ")
    assert svg.endswith("</svg>")
    assert "GATE EE Practice Paper" in svg
    ET.fromstring(svg)


def test_question_blocks_are_inside_page():
    result = QuestionPaperRenderer().render(simple_paper())
    report = validate_rendered_paper(result)
    assert report["valid"] is True
    assert report["questions"] == 3


def test_m19_layout_contract_is_consumed():
    result = QuestionPaperRenderer().render(simple_paper())
    assert all(item.kind == "question_block" for page in result.pages for item in page.items)
    assert all(item.metadata["page"] == page.number for page in result.pages for item in page.items)


def test_math_text_is_formatted_without_wrapping_entire_prose():
    result = QuestionPaperRenderer().render(simple_paper())
    svg = result.pages[0].svg
    assert "For $z=2+3i$, find $|z|$." in svg
    assert "For $z=2+3i$, find $|z|$." in svg or "For z=2+3i, find |z|." in svg


def test_options_are_rendered():
    result = QuestionPaperRenderer().render(simple_paper())
    svg = result.pages[0].svg
    for label in ["A.", "B.", "C.", "D."]:
        assert label in svg


def test_diagram_is_embedded_and_not_missing():
    result = QuestionPaperRenderer().render(simple_paper())
    svg = result.pages[0].svg
    assert '<svg x="' in svg
    assert "Points" in svg
    assert "NaN" not in svg


def test_multiple_pages_are_created_without_splitting_questions():
    questions = [QuestionSpec(f"q{i}", "Find the value of $x^2+1$." * 4, number=i, marks=1) for i in range(1, 30)]
    paper = PaperSpec("Long Paper", questions=questions)
    result = QuestionPaperRenderer().render(paper)
    assert len(result.pages) > 1
    all_ids = [item.id for page in result.pages for item in page.items]
    assert all_ids == [q.id for q in questions]


def test_question_too_tall_is_rejected():
    options = PaperRenderOptions(diagram_height=2000)
    paper = PaperSpec("Too tall", [QuestionSpec("q1", "Draw it", diagrams=[DiagramSpec("graph", coordinate_system="cartesian", axes=[Axis("x"), Axis("y")])])])
    with pytest.raises(ValueError, match="taller than one printable page"):
        QuestionPaperRenderer(options).render(paper)


def test_duplicate_question_ids_rejected():
    paper = PaperSpec("Bad", [QuestionSpec("q1", "a"), QuestionSpec("q1", "b")])
    with pytest.raises(ValueError, match="unique"):
        paper.ensure_valid()


def test_structured_dictionary_input():
    data = {
        "title": "Structured",
        "questions": [
            {"id": "q1", "text": "Draw a block diagram.", "number": 1,
             "diagrams": [{"diagram_type": "block_diagram",
                            "nodes": [{"id": "A", "kind": "block", "label": "Input"},
                                      {"id": "B", "kind": "block", "label": "Output"}],
                            "edges": [{"source": "A", "target": "B", "kind": "signal"}]}]}
        ],
    }
    result = render_question_paper(data)
    assert result["paper"]["page_count"] == 1
    assert result["output_path"] is None



def test_engineering_diagram_is_embedded():
    paper = PaperSpec(
        "Engineering Paper",
        questions=[QuestionSpec(
            "q1", "Study the block diagram.", number=1, marks=2,
            diagrams=[DiagramSpec(
                "block_diagram",
                title="Input to Output",
                nodes=[Node("A", "block", "Input"), Node("B", "block", "Output")],
                edges=[Edge("A", "B", "signal", directed=True)],
            )],
        )],
    )
    result = QuestionPaperRenderer().render(paper)
    svg = result.pages[0].svg
    assert "Input" in svg and "Output" in svg
    ET.fromstring(svg)


def test_section_heading_is_rendered():
    paper = PaperSpec("Sections", [QuestionSpec("q1", "Find $x$.", number=1, section="Section A")])
    svg = QuestionPaperRenderer().render(paper).pages[0].svg
    assert "Section A" in svg


def test_rendered_manifest_identifies_m20_and_m19():
    result = QuestionPaperRenderer().render(simple_paper())
    assert result.manifest["engine"] == "M20"
    assert result.manifest["source_layout_engine"] == "M19"

def test_validator_public_api():
    assert validate_question_paper(simple_paper()) is True


def test_paper_input_is_not_modified():
    paper = simple_paper()
    before = copy.deepcopy(paper.to_dict())
    QuestionPaperRenderer().render(paper)
    assert paper.to_dict() == before
