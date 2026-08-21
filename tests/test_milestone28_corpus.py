"""Milestone 28 — real-world corpus compatibility contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.public_api import compile_paper, get_input_sha256, verify_compilation

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "input" / "milestone28_real_world_corpus.json"


def load_corpus():
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    assert data["contract"] == "M28"
    assert data["version"] == "28.0"
    assert data["case_count"] == len(data["papers"]) == 20
    return data


def files(out):
    return {p.name: p.read_bytes() for p in out.iterdir() if p.is_file()}


def test_corpus_is_broad_and_unique():
    data = load_corpus()
    ids = [p["metadata"]["case_id"] for p in data["papers"]]
    families = [p["metadata"]["family"] for p in data["papers"]]
    assert len(ids) == len(set(ids)) == 20
    assert len(set(families)) == 20
    assert set(data["families"]) == set(families)
    assert all(len(p["questions"]) >= 3 for p in data["papers"])


@pytest.mark.parametrize("paper", load_corpus()["papers"], ids=lambda p: p["metadata"]["case_id"])
def test_every_corpus_paper_compiles_to_all_production_formats(tmp_path, paper):
    out = tmp_path / paper["metadata"]["case_id"]
    result = compile_paper(paper, out, formats=("markdown", "svg", "pdf", "html"))
    assert result.success
    assert result.question_count == len(paper["questions"])
    assert result.total_marks == pytest.approx(6)
    assert result.input_sha256 == get_input_sha256(paper)
    assert {a.path for a in result.artifacts} == {"paper.md", "paper.svg", "paper.pdf", "paper.html", "manifest.json"}
    report = verify_compilation(out, expected_input_sha256=result.input_sha256)
    assert report["valid"] is True
    assert report["artifact_count"] == 4

    md = (out / "paper.md").read_text(encoding="utf-8")
    html = (out / "paper.html").read_text(encoding="utf-8")
    pdf = (out / "paper.pdf").read_bytes()
    svg = (out / "paper.svg").read_text(encoding="utf-8")
    assert md.startswith("# M28 ")
    assert "## Questions" in md
    assert "NaN" not in md
    assert "<html" in html.lower() and "</html>" in html.lower()
    assert pdf.startswith(b"%PDF-") and b"%%EOF" in pdf
    assert svg.startswith("<svg ") and svg.endswith("</svg>")
    assert "NaN" not in svg and "undefined" not in svg


def test_m28_compilation_is_deterministic_for_representative_corpus(tmp_path):
    papers = load_corpus()["papers"]
    for paper in (papers[0], papers[9], papers[-1]):
        a = tmp_path / (paper["metadata"]["case_id"] + "-a")
        b = tmp_path / (paper["metadata"]["case_id"] + "-b")
        compile_paper(paper, a)
        compile_paper(paper, b)
        assert files(a) == files(b)


def test_m28_unicode_case_preserves_unicode(tmp_path):
    paper = next(p for p in load_corpus()["papers"] if p["metadata"]["family"] == "unicode")
    out = tmp_path / "unicode"
    compile_paper(paper, out, formats=("markdown",))
    text = (out / "paper.md").read_text(encoding="utf-8")
    assert "\\pi" in text and "\\leq" in text and "∑" in text


def test_m28_diagram_case_reaches_svg_and_markdown(tmp_path):
    paper = next(p for p in load_corpus()["papers"] if p["metadata"]["family"] == "diagram")
    out = tmp_path / "diagram"
    compile_paper(paper, out, formats=("markdown", "svg"))
    md = (out / "paper.md").read_text(encoding="utf-8")
    svg = (out / "paper.svg").read_text(encoding="utf-8")
    assert "M28 Coordinate Figure" in md
    assert svg.startswith("<svg ") and "NaN" not in svg


def test_m28_manifest_hashes_match_artifacts(tmp_path):
    paper = load_corpus()["papers"][0]
    out = tmp_path / "manifest"
    compile_paper(paper, out)
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    for item in manifest["artifacts"]:
        data = (out / item["path"]).read_bytes()
        assert len(data) == item["bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"]


def test_m28_malformed_question_fails_closed(tmp_path):
    paper = load_corpus()["papers"][0]
    broken = json.loads(json.dumps(paper))
    broken["questions"][0]["text"] = ""
    with pytest.raises(ValueError):
        compile_paper(broken, tmp_path / "broken")
    assert not (tmp_path / "broken").exists()
