"""Milestone 29 — formatter completeness and edge-case closure."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.math_normalizer import normalize_expression, validate_expression
from src.public_api import compile_paper, format_markdown, validate_markdown

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "input" / "milestone28_real_world_corpus.json"


def corpus_paper():
    return json.loads(CORPUS.read_text(encoding="utf-8"))["papers"][0]


@pytest.mark.parametrize(
    "source, expected",
    [
        (r"\operatorname{rank}(A) + \operatorname{det}(B)", r"\mathrm{rank}(A) + \mathrm{det}(B)"),
        ("π ≤ x ≥ 0", r"\pi  \leq  x \geq  0"),
        ("α² + β³", r"\alpha ^2 + \beta ^3"),
        ("x¹ + y₄", "x^1 + y_4"),
        ("a ± b × c ÷ d", r"a \pm  b \times  c \div  d"),
        ("x − y → z", r"x - y \to  z"),
        ("P ⇒ Q ⇔ R", r"P \Rightarrow  Q \Leftrightarrow  R"),
        (r"\dfrac{a}{b}", r"\frac{a}{b}"),
        (r"\operatorname{rank}(A) + \operatorname{det}(B)", r"\mathrm{rank}(A) + \mathrm{det}(B)"),
    ],
)
def test_m29_math_normalization_edge_cases(source, expected):
    assert normalize_expression(source) == expected


def test_m29_validation_rejects_unbalanced_structures():
    result = validate_expression(r"\frac{a}{b")
    assert result.valid is False
    assert any("Unbalanced" in warning for warning in result.warnings)


def test_m29_validation_rejects_unbalanced_left_right():
    result = validate_expression(r"\left( x + 1")
    assert result.valid is False
    assert any("left" in warning for warning in result.warnings)


def test_m29_validation_rejects_unbalanced_display_delimiters():
    result = validate_expression(r"x^2 $$")
    assert result.valid is False
    assert any("display-math" in warning for warning in result.warnings)


def test_m29_public_formatter_normalizes_mixed_unicode_and_operators():
    source = "## Question\n\nEvaluate π × x² − 1 and compare it with \\operatorname{det}(A)."
    output = format_markdown(source)
    assert r"\operatorname" not in output
    assert r"\mathrm{det}" in output
    assert r"\pi" in output
    assert r"\times" in output
    assert "x^2" in output
    assert "−" not in output


def test_m29_public_validation_is_fail_closed_for_unbalanced_math():
    source = "## Question\n\nFind $$\\frac{a}{b$$."
    result = validate_markdown(source)
    assert result.valid is False
    assert any(not check["passed"] for check in result.checks)


def test_m29_formatter_is_stable_across_line_endings():
    source = "## Question\n\nFind x².\n"
    assert format_markdown(source) == format_markdown(source.replace("\n", "\r\n"))


def test_m29_structured_pipeline_rejects_empty_question_before_output(tmp_path):
    paper = corpus_paper()
    broken = json.loads(json.dumps(paper))
    broken["questions"][0]["text"] = "   "
    with pytest.raises(ValueError, match="text must not be empty"):
        compile_paper(broken, tmp_path / "broken", formats=("markdown",))
    assert not (tmp_path / "broken").exists()


def test_m29_structured_pipeline_rejects_duplicate_question_ids(tmp_path):
    paper = corpus_paper()
    broken = json.loads(json.dumps(paper))
    broken["questions"][1]["id"] = broken["questions"][0]["id"]
    with pytest.raises(ValueError, match="unique"):
        compile_paper(broken, tmp_path / "duplicate", formats=("markdown",))
    assert not (tmp_path / "duplicate").exists()


def test_m29_structured_pipeline_rejects_invalid_format_without_output(tmp_path):
    paper = corpus_paper()
    with pytest.raises(ValueError, match="Unsupported output format"):
        compile_paper(paper, tmp_path / "invalid", formats=("markdown", "docx"))
    assert not (tmp_path / "invalid").exists()


def test_m29_markdown_contract_preserves_questions_and_options(tmp_path):
    paper = corpus_paper()
    paper = json.loads(json.dumps(paper))
    paper["questions"][0]["options"] = ["α", "β", "γ", "δ"]
    out = tmp_path / "paper"
    result = compile_paper(paper, out, formats=("markdown",))
    assert result.success
    text = (out / "paper.md").read_text(encoding="utf-8")
    assert "## Questions" in text
    assert r"A. \alpha" in text
    assert r"D. \delta" in text


def test_m29_malformed_corpus_case_does_not_leave_partial_output(tmp_path):
    paper = corpus_paper()
    broken = json.loads(json.dumps(paper))
    broken["title"] = ""
    out = tmp_path / "malformed"
    with pytest.raises(ValueError):
        compile_paper(broken, out)
    assert not out.exists()
