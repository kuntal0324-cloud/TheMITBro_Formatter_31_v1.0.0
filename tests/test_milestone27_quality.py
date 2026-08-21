"""Milestone 27 — production-quality end-to-end validation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.public_api import (
    API_VERSION,
    BUILD_CONTRACT_VERSION,
    INPUT_SCHEMA_VERSION,
    compile_paper,
    format_markdown,
    get_input_sha256,
    validate_markdown,
    verify_compilation,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "input" / "milestone27_quality_corpus.json"


def load_corpus():
    return json.loads(CORPUS.read_text(encoding="utf-8"))["papers"]


def artifact_bytes(directory: Path):
    return {
        path.name: path.read_bytes()
        for path in sorted(directory.iterdir())
        if path.is_file()
    }


def assert_common_artifacts(out: Path):
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["build_contract"] == BUILD_CONTRACT_VERSION
    assert manifest["input_schema_version"] == INPUT_SCHEMA_VERSION
    assert manifest["deterministic"] is True
    assert manifest["artifact_count"] >= 1

    for item in manifest["artifacts"]:
        path = out / item["path"]
        assert path.is_file()
        data = path.read_bytes()
        assert len(data) == item["bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"]

    if (out / "paper.svg").exists():
        svg = (out / "paper.svg").read_text(encoding="utf-8")
        assert svg.startswith("<svg ")
        assert svg.endswith("</svg>")
        assert "NaN" not in svg
        assert "undefined" not in svg

    if (out / "paper.html").exists():
        html = (out / "paper.html").read_text(encoding="utf-8")
        assert "<html" in html.lower()
        assert "</html>" in html.lower()
        assert "undefined" not in html.lower()

    if (out / "paper.pdf").exists():
        assert (out / "paper.pdf").read_bytes().startswith(b"%PDF")

    if (out / "paper.md").exists():
        markdown = (out / "paper.md").read_text(encoding="utf-8")
        assert markdown.startswith("# ")
        assert "## Questions" in markdown
        assert "NaN" not in markdown


def test_m27_public_contract_is_frozen():
    assert API_VERSION == "1.0"
    assert BUILD_CONTRACT_VERSION == "26.0"
    assert INPUT_SCHEMA_VERSION == "1.0"


@pytest.mark.parametrize("paper", load_corpus(), ids=lambda p: p["metadata"]["case_id"])
def test_m27_full_pipeline_for_representative_papers(tmp_path, paper):
    out = tmp_path / paper["metadata"]["case_id"]
    result = compile_paper(
        paper,
        out,
        formats=("markdown", "svg", "pdf", "html"),
    )

    assert result.success
    assert result.question_count == len(paper["questions"])
    assert result.total_marks == pytest.approx(
        paper.get("total_marks")
        if paper.get("total_marks") is not None
        else sum(q.get("marks", 0) for q in paper["questions"])
    )
    assert result.input_sha256 == get_input_sha256(paper)
    assert_common_artifacts(out)

    report = verify_compilation(
        out,
        expected_input_sha256=result.input_sha256,
    )
    assert report["valid"] is True
    assert report["artifact_count"] == 4


def test_m27_deterministic_artifacts(tmp_path):
    paper = load_corpus()[2]
    left = tmp_path / "left"
    right = tmp_path / "right"

    compile_paper(paper, left)
    compile_paper(paper, right)

    assert artifact_bytes(left) == artifact_bytes(right)


def test_m27_selected_formats_have_no_extra_production_files(tmp_path):
    paper = load_corpus()[0]
    out = tmp_path / "selected"

    result = compile_paper(paper, out, formats=("markdown", "html"))

    assert {a.path for a in result.artifacts} == {
        "paper.md", "paper.html", "manifest.json"
    }
    assert set(p.name for p in out.iterdir()) == {
        "paper.md", "paper.html", "manifest.json"
    }
    assert_common_artifacts(out)
    assert not (out / "paper.pdf").exists()
    assert not (out / "paper.svg").exists()


def test_m27_public_markdown_api_round_trip():
    source = "# Question\n\nFind $x^2$.\n"
    formatted = format_markdown(source)

    assert isinstance(formatted, str)
    assert formatted
    validation = validate_markdown(source)
    assert validation.valid is True
    assert validation.formatted == formatted
    assert all("name" in check and "passed" in check for check in validation.checks)


def test_m27_unicode_survives_markdown_generation(tmp_path):
    paper = load_corpus()[1]
    out = tmp_path / "unicode"
    compile_paper(paper, out, formats=("markdown",))

    text = (out / "paper.md").read_text(encoding="utf-8")
    assert "π" in text or r"\pi" in text
    assert "∑" in text
    assert "≤" in text or r"\leq" in text
    assert "## Instructions" in text


def test_m27_diagrams_survive_end_to_end(tmp_path):
    paper = load_corpus()[2]
    out = tmp_path / "diagram"
    compile_paper(paper, out, formats=("markdown", "svg"))

    markdown = (out / "paper.md").read_text(encoding="utf-8")
    svg = (out / "paper.svg").read_text(encoding="utf-8")

    assert "_Diagram: Coordinate regression_" in markdown
    assert "_Diagram: Signal path_" in markdown
    assert svg.startswith("<svg ")
    assert "NaN" not in svg
    assert "undefined" not in svg


def test_m27_invalid_input_fails_before_output_replacement(tmp_path):
    paper = load_corpus()[0]
    out = tmp_path / "safe"
    compile_paper(paper, out, formats=("markdown",))
    previous = (out / "paper.md").read_bytes()

    invalid = dict(paper)
    invalid["questions"] = []

    with pytest.raises(ValueError):
        compile_paper(invalid, out, formats=("pdf",))

    assert (out / "paper.md").read_bytes() == previous
    assert not (out / "paper.pdf").exists()


def test_m27_invalid_format_fails_without_touching_output(tmp_path):
    paper = load_corpus()[0]
    out = tmp_path / "safe"
    compile_paper(paper, out, formats=("markdown",))
    previous = artifact_bytes(out)

    with pytest.raises(ValueError, match="Unsupported output format"):
        compile_paper(paper, out, formats=("markdown", "docx"))

    assert artifact_bytes(out) == previous


@pytest.mark.parametrize(
    "bad",
    [
        {"schema_version": "9.0"},
        {"title": "", "questions": [{"id": "q", "text": "x"}]},
        {"title": "x", "questions": []},
    ],
)
def test_m27_rejects_invalid_structured_papers(tmp_path, bad):
    base = load_corpus()[0]
    paper = dict(base)
    paper.update(bad)

    with pytest.raises((ValueError, TypeError)):
        compile_paper(paper, tmp_path / "invalid")


def test_m27_verify_is_read_only(tmp_path):
    out = tmp_path / "bundle"
    result = compile_paper(load_corpus()[0], out, formats=("markdown", "svg"))
    before = artifact_bytes(out)

    report = verify_compilation(out, expected_input_sha256=result.input_sha256)

    assert report["valid"] is True
    assert artifact_bytes(out) == before


def test_m27_manifest_declares_only_real_artifacts(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_corpus()[0], out, formats=("markdown", "pdf"))
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))

    listed = {item["path"] for item in manifest["artifacts"]}
    actual = {p.name for p in out.iterdir() if p.is_file()} - {"manifest.json"}
    assert listed == actual


def test_m27_output_target_must_be_directory(tmp_path):
    target = tmp_path / "file"
    target.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="not a directory"):
        compile_paper(load_corpus()[0], target)


def test_m27_input_identity_is_stable_for_equivalent_mapping_order(tmp_path):
    paper = load_corpus()[0]
    reordered = dict(reversed(list(paper.items())))

    assert get_input_sha256(paper) == get_input_sha256(reordered)

    left = tmp_path / "left"
    right = tmp_path / "right"
    compile_paper(paper, left, formats=("markdown",))
    compile_paper(reordered, right, formats=("markdown",))
    assert artifact_bytes(left) == artifact_bytes(right)
