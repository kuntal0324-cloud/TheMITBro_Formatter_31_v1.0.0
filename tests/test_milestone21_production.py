import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from src.question_paper_ir import PaperSpec, QuestionSpec
from src.question_paper_renderer import QuestionPaperRenderer
from src.question_paper_validator import validate_rendered_paper
from src.pdf_production import render_paper_pdf
from src.html_production import render_paper_html


def sample_paper():
    return PaperSpec(
        title="TheMITbro M21 Production Test",
        subject="Electrical Engineering",
        exam="TheMITbro",
        duration_minutes=60,
        total_marks=5,
        instructions=["Answer all questions."],
        questions=[
            QuestionSpec("q1", "Find $2+3$.", number=1, marks=2),
            QuestionSpec("q2", "For $z=2+3i$, find $|z|$.", number=2, marks=3),
        ],
    )


def test_pdf_production_creates_valid_nonempty_pdf(tmp_path):
    out = tmp_path / "paper.pdf"
    result = render_paper_pdf(sample_paper(), out)
    assert result == out
    data = out.read_bytes()
    assert data.startswith(b"%PDF-")
    assert b"%%EOF" in data
    assert out.stat().st_size > 1000


def test_pdf_production_is_deterministic(tmp_path):
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    render_paper_pdf(sample_paper(), a)
    render_paper_pdf(sample_paper(), b)
    assert a.read_bytes() == b.read_bytes()


def test_html_production_is_self_contained(tmp_path):
    out = tmp_path / "paper.html"
    render_paper_html(sample_paper(), out)
    text = out.read_text(encoding="utf-8")
    assert text.startswith("<!doctype html>")
    assert "<svg " in text
    assert "<script src=" not in text
    assert "M20" in text
    assert "M21" in text


def test_html_contains_each_page(tmp_path):
    paper = sample_paper()
    result = QuestionPaperRenderer().render(paper)
    out = tmp_path / "paper.html"
    render_paper_html(paper, out)
    text = out.read_text(encoding="utf-8")
    assert text.count('class="paper-page"') == len(result.pages)


def test_m20_validation_remains_clean():
    result = QuestionPaperRenderer().render(sample_paper())
    assert validate_rendered_paper(result)["valid"]


def test_html_manifest_is_machine_readable(tmp_path):
    out = tmp_path / "paper.html"
    render_paper_html(sample_paper(), out)
    text = out.read_text(encoding="utf-8")
    assert 'id="themitbro-manifest"' in text
    assert '"engine":"M20"' in text
    assert '"deterministic":true' in text


def test_output_parent_is_created(tmp_path):
    out = tmp_path / "nested" / "deep" / "paper.pdf"
    render_paper_pdf(sample_paper(), out)
    assert out.exists()


def test_pdf_and_html_accept_dictionary_input(tmp_path):
    data = sample_paper().to_dict()
    pdf = tmp_path / "dict.pdf"
    html = tmp_path / "dict.html"
    render_paper_pdf(data, pdf)
    render_paper_html(data, html)
    assert pdf.exists() and html.exists()
