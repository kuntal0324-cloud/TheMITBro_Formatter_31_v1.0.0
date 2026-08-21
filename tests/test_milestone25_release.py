"""Milestone 25 - public API contract and end-to-end compilation."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from src.public_api import API_VERSION, compile_paper, format_markdown, validate_markdown
from src.question_compiler import COMPILER_VERSION, SUPPORTED_FORMATS


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "input" / "milestone25_e2e_paper.json"


def load_paper():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_public_api_contract_is_explicit():
    assert API_VERSION == "1.0"
    assert COMPILER_VERSION == "25.0"
    assert SUPPORTED_FORMATS == ("markdown", "svg", "pdf", "html")


def test_public_markdown_api_preserves_legacy_behavior():
    source = r"For A, use $\operatorname{det}(A)=1$."
    formatted = format_markdown(source)
    assert r"\operatorname" not in formatted
    assert r"\mathrm{det}" in formatted


def test_public_validation_api_returns_structured_result():
    result = validate_markdown(r"For A, use $\operatorname{det}(A)=1$.")
    assert result.valid is True
    data = result.to_dict()
    assert data["valid"] is True
    assert all("name" in item and "passed" in item for item in data["checks"])


def test_public_validation_rejects_invalid_document():
    result = validate_markdown("$$x+1")
    assert result.valid is False
    assert any(item["passed"] is False for item in result.checks)


def test_compilation_result_and_artifact_are_serializable():
    from src.question_compiler import CompilationArtifact, CompilationResult

    artifact = CompilationArtifact("markdown", "paper.md", "abc", 3)
    assert artifact.to_dict() == {
        "kind": "markdown",
        "path": "paper.md",
        "sha256": "abc",
        "bytes": 3,
    }

    result = CompilationResult(
        "COMPILED", "25.0", "1.0", 1, 1, 2.0, "out", (artifact,)
    )
    assert result.success is True
    assert result.to_dict()["artifacts"][0]["path"] == "paper.md"


def test_public_api_type_contracts():
    with pytest.raises(TypeError, match="text must be a string"):
        format_markdown(123)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="paper must be a mapping"):
        compile_paper([], "unused")  # type: ignore[arg-type]


def test_compiler_rejects_unsupported_schema_version(tmp_path):
    paper = load_paper()
    paper["schema_version"] = "2.0"
    with pytest.raises(ValueError, match="schema_version"):
        compile_paper(paper, tmp_path / "out")


def test_compiler_rejects_bad_formats(tmp_path):
    with pytest.raises(ValueError, match="At least one"):
        compile_paper(load_paper(), tmp_path / "out", formats=())

    with pytest.raises(ValueError, match="unique"):
        compile_paper(load_paper(), tmp_path / "out", formats=("pdf", "pdf"))

    with pytest.raises(ValueError, match="Unsupported"):
        compile_paper(load_paper(), tmp_path / "out", formats=("docx",))


def test_compiler_rejects_non_sequence_formats(tmp_path):
    with pytest.raises(TypeError, match="formats must be a sequence"):
        compile_paper(load_paper(), tmp_path / "out", formats="pdf")  # type: ignore[arg-type]


def test_end_to_end_compilation_produces_all_contract_artifacts(tmp_path):
    out = tmp_path / "compiled"
    result = compile_paper(load_paper(), out)

    assert result.success
    assert result.status == "COMPILED"
    assert result.api_contract == "1.0"
    assert result.compiler_version == "25.0"
    assert result.question_count == 12
    assert result.page_count >= 1
    assert result.total_marks == 24

    expected = {"paper.md", "paper.svg", "paper.pdf", "paper.html", "manifest.json"}
    assert {item.path for item in result.artifacts} == expected
    assert {p.name for p in out.iterdir()} == expected

    assert (out / "paper.svg").read_text(encoding="utf-8").startswith("<svg ")
    assert (out / "paper.pdf").read_bytes().startswith(b"%PDF-")
    assert "<svg " in (out / "paper.html").read_text(encoding="utf-8")

    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["deterministic"] is True
    assert manifest["question_count"] == 12
    assert {item["path"] for item in manifest["artifacts"]} == {
        "paper.md", "paper.svg", "paper.pdf", "paper.html"
    }


def test_end_to_end_compilation_is_deterministic(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    result_a = compile_paper(load_paper(), a)
    result_b = compile_paper(load_paper(), b)

    hashes_a = {item.path: item.sha256 for item in result_a.artifacts}
    hashes_b = {item.path: item.sha256 for item in result_b.artifacts}
    assert hashes_a == hashes_b

    for name in ("paper.md", "paper.svg", "paper.pdf", "paper.html", "manifest.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()


def test_compiler_supports_selected_formats(tmp_path):
    out = tmp_path / "selected"
    result = compile_paper(load_paper(), out, formats=("markdown", "pdf"))
    assert {item.path for item in result.artifacts} == {"paper.md", "paper.pdf", "manifest.json"}
    assert (out / "paper.md").is_file()
    assert (out / "paper.pdf").is_file()
    assert not (out / "paper.svg").exists()
    assert not (out / "paper.html").exists()


def test_compiler_replaces_existing_output_only_after_success(tmp_path):
    out = tmp_path / "existing"
    out.mkdir()
    (out / "stale.txt").write_text("old", encoding="utf-8")
    stale_dir = out / "stale-dir"
    stale_dir.mkdir()
    (stale_dir / "old.txt").write_text("old", encoding="utf-8")
    compile_paper(load_paper(), out, formats=("markdown",))
    assert not (out / "stale.txt").exists()
    assert (out / "paper.md").exists()

    bad = dict(load_paper())
    bad["questions"] = []
    with pytest.raises(ValueError):
        compile_paper(bad, out, formats=("pdf",))
    assert (out / "paper.md").exists()


def test_cli_version():
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--version"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "API 1.0 / M25" in result.stdout


def test_cli_end_to_end_compile(tmp_path):
    out = tmp_path / "cli-output"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.main",
            "--compile-json",
            str(FIXTURE),
            "--output-dir",
            str(out),
            "--formats",
            "markdown,pdf,html",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Status: COMPILED" in result.stdout
    assert "Artifacts: 4" in result.stdout
    assert (out / "paper.md").exists()
    assert (out / "paper.pdf").exists()
    assert (out / "paper.html").exists()
    assert (out / "manifest.json").exists()
    assert not (out / "paper.svg").exists()


def test_cli_compile_requires_output_dir():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.main",
            "--compile-json",
            str(FIXTURE),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "requires --output-dir" in result.stderr


def test_compiler_rejects_file_output_path(tmp_path):
    target = tmp_path / "not-a-directory"
    target.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="not a directory"):
        compile_paper(load_paper(), target, formats=("markdown",))
