"""Milestone 26 — reproducible build and artifact-integrity contract."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from src.public_api import (
    BUILD_CONTRACT_VERSION,
    INPUT_SCHEMA_VERSION,
    compile_paper,
    get_input_sha256,
    verify_compilation,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "input" / "milestone25_e2e_paper.json"


def load_paper():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_m26_contract_constants():
    assert BUILD_CONTRACT_VERSION == "26.0"
    assert INPUT_SCHEMA_VERSION == "1.0"


def test_input_hash_is_order_independent():
    a = {"title": "T", "questions": [{"id": "Q1", "text": "x"}]}
    b = {"questions": [{"text": "x", "id": "Q1"}], "title": "T"}
    assert get_input_sha256(a) == get_input_sha256(b)


def test_input_hash_changes_when_content_changes():
    a = {"title": "T", "questions": [{"id": "Q1", "text": "x"}]}
    b = {"title": "T", "questions": [{"id": "Q1", "text": "y"}]}
    assert get_input_sha256(a) != get_input_sha256(b)


def test_input_hash_rejects_non_json_values():
    with pytest.raises(TypeError, match="JSON-serializable"):
        get_input_sha256({"title": "T", "bad": object()})


def test_compile_writes_m26_manifest(tmp_path):
    out = tmp_path / "bundle"
    result = compile_paper(load_paper(), out, formats=("markdown", "svg"))

    assert result.build_contract == "26.0"
    assert len(result.input_sha256) == 64
    assert result.input_sha256 == get_input_sha256(load_paper())

    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["build_contract"] == "26.0"
    assert manifest["input_schema_version"] == "1.0"
    assert manifest["input_sha256"] == result.input_sha256
    assert manifest["artifact_count"] == 2


def test_verify_compilation_accepts_valid_bundle(tmp_path):
    paper = load_paper()
    out = tmp_path / "bundle"
    result = compile_paper(paper, out)

    report = verify_compilation(
        str(out),
        expected_input_sha256=result.input_sha256,
    )

    assert report["valid"] is True
    assert report["build_contract"] == "26.0"
    assert report["artifact_count"] == 4
    assert set(report["checked_artifacts"]) == {
        "paper.md", "paper.svg", "paper.pdf", "paper.html"
    }


def test_verify_compilation_rejects_tampered_artifact(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out)

    (out / "paper.md").write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ValueError, match="mismatch"):
        verify_compilation(str(out))


def test_verify_compilation_rejects_extra_file(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown",))
    (out / "unexpected.txt").write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="unexpected or missing"):
        verify_compilation(str(out))


def test_verify_compilation_rejects_input_identity_mismatch(tmp_path):
    out = tmp_path / "bundle"
    result = compile_paper(load_paper(), out, formats=("markdown",))

    wrong_hash = "0" * 64
    assert wrong_hash != result.input_sha256

    with pytest.raises(ValueError, match="input identity"):
        verify_compilation(str(out), expected_input_sha256=wrong_hash)


def test_verify_compilation_rejects_manifest_tampering(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown",))

    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["question_count"] = 999
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="manifest"):
        verify_compilation(str(out))


def test_cli_verify_output(tmp_path):
    from src import main as main_module
    from types import SimpleNamespace

    out = tmp_path / "bundle"
    result = compile_paper(load_paper(), out, formats=("markdown",))

    args = SimpleNamespace(
        verify_output=out,
        expected_input_sha256=result.input_sha256,
    )

    assert main_module._run_verify(args) == 0



def test_cli_verify_missing_output_dir(tmp_path):
    from src import main as main_module
    from types import SimpleNamespace

    with pytest.raises(ValueError, match="not a directory"):
        main_module._run_verify(
            SimpleNamespace(
                verify_output=tmp_path / "missing",
                expected_input_sha256=None,
            )
        )


def _rewrite_manifest(out: Path, mutate):
    from src.question_compiler import _manifest_sha256

    path = out / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mutate(manifest)
    manifest["manifest_sha256"] = _manifest_sha256(manifest)
    path.write_text(
        json.dumps(
            manifest,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )


def test_compiler_direct_type_rejection():
    from src.question_compiler import compile_paper

    with pytest.raises(TypeError, match="paper must be a mapping"):
        compile_paper([], "unused")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda m: m.pop("question_count"), "missing fields"),
        (lambda m: m.update(build_contract="25.0"), "Unsupported build contract"),
        (lambda m: m.update(input_schema_version="9.0"), "Unsupported input schema"),
        (lambda m: m.update(deterministic=False), "deterministic=true"),
        (lambda m: m.update(artifact_count=999), "artifact_count"),
        (lambda m: m.update(artifacts=[]), "at least one artifact"),
    ],
)
def test_manifest_contract_rejections(tmp_path, mutate, message):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown",))

    _rewrite_manifest(out, mutate)

    with pytest.raises(ValueError, match=message):
        verify_compilation(str(out))


def test_manifest_invalid_self_hash(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown",))

    path = out / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["manifest_sha256"] = "bad"
    path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid manifest SHA"):
        verify_compilation(str(out))


def test_manifest_self_hash_mismatch(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown",))

    path = out / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["manifest_sha256"] = "0" * 64
    path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="manifest hash mismatch"):
        verify_compilation(str(out))


def test_manifest_invalid_json(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown",))
    (out / "manifest.json").write_text("{not-json", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid JSON"):
        verify_compilation(str(out))


def test_manifest_missing_file(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown",))
    (out / "manifest.json").unlink()

    with pytest.raises(ValueError, match="manifest is missing"):
        verify_compilation(str(out))


def test_manifest_missing_artifact(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown",))
    (out / "paper.md").unlink()

    with pytest.raises(ValueError, match="Missing artifact"):
        verify_compilation(str(out))


def test_manifest_invalid_artifact_path(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown",))

    _rewrite_manifest(
        out,
        lambda m: m["artifacts"][0].update(path="../paper.md"),
    )

    with pytest.raises(ValueError, match="Invalid artifact path"):
        verify_compilation(str(out))


def test_manifest_duplicate_artifact_paths(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown", "svg"))

    def duplicate(m):
        m["artifacts"][1]["path"] = m["artifacts"][0]["path"]
        m["artifacts"][1]["sha256"] = m["artifacts"][0]["sha256"]
        m["artifacts"][1]["bytes"] = m["artifacts"][0]["bytes"]
        m["artifact_count"] = len(m["artifacts"])

    _rewrite_manifest(out, duplicate)

    with pytest.raises(ValueError, match="duplicate artifact paths"):
        verify_compilation(str(out))


def test_manifest_invalid_input_hash(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown",))

    _rewrite_manifest(out, lambda m: m.update(input_sha256="bad"))

    with pytest.raises(ValueError, match="invalid input SHA"):
        verify_compilation(str(out))


def test_manifest_byte_count_mismatch(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown",))

    _rewrite_manifest(
        out,
        lambda m: m["artifacts"][0].update(
            bytes=m["artifacts"][0]["bytes"] + 1
        ),
    )

    with pytest.raises(ValueError, match="byte count mismatch"):
        verify_compilation(str(out))


def test_manifest_artifact_hash_mismatch(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown",))

    _rewrite_manifest(
        out,
        lambda m: m["artifacts"][0].update(sha256="0" * 64),
    )

    with pytest.raises(ValueError, match="Artifact hash mismatch"):
        verify_compilation(str(out))


def test_manifest_noncanonical_serialization(tmp_path):
    out = tmp_path / "bundle"
    compile_paper(load_paper(), out, formats=("markdown",))

    path = out / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    # Keep semantic content and self-hash intact, but change serialization.
    path.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="canonically serialized"):
        verify_compilation(str(out))


def test_paper_markdown_instructions_sections_and_diagrams(tmp_path):
    from src.question_compiler import _paper_markdown
    from src.question_paper_ir import PaperSpec, QuestionSpec
    from src.diagram_ir import Axis, DiagramSpec

    paper = PaperSpec(
        title="T",
        exam="GATE",
        subject="EE",
        duration_minutes=60,
        instructions=["Use SI units."],
        questions=[
            QuestionSpec(
                id="Q1",
                text="Solve $x+1=2$.",
                number=7,
                marks=2,
                section="A",
                diagrams=[
                    DiagramSpec(
                        diagram_type="graph",
                        title="Graph",
                        coordinate_system="cartesian",
                        axes=[Axis("x"), Axis("y")],
                    )
                ],
            )
        ],
    )
    markdown = _paper_markdown(paper)
    assert "## Instructions" in markdown
    assert "**Section:** A" in markdown
    assert "_Diagram: Graph_" in markdown
    assert "**Exam:** GATE" in markdown


def test_compile_all_requested_formats_and_manifest(tmp_path):
    from src.question_compiler import compile_paper

    out = tmp_path / "bundle"
    result = compile_paper(load_paper(), out, formats=("markdown", "svg", "pdf", "html"))
    assert len(result.artifacts) == 5
    assert (out / "manifest.json").is_file()


def test_compile_selected_svg_only(tmp_path):
    from src.question_compiler import compile_paper

    out = tmp_path / "bundle"
    result = compile_paper(load_paper(), out, formats=("svg",))
    assert {item.path for item in result.artifacts} == {"paper.svg", "manifest.json"}
    assert (out / "paper.svg").is_file()


def test_compile_selected_html_only(tmp_path):
    from src.question_compiler import compile_paper

    out = tmp_path / "bundle"
    result = compile_paper(load_paper(), out, formats=("html",))
    assert {item.path for item in result.artifacts} == {"paper.html", "manifest.json"}
    assert (out / "paper.html").is_file()


def test_compile_schema_version_rejection(tmp_path):
    paper = load_paper()
    paper["schema_version"] = "2.0"

    from src.question_compiler import compile_paper

    with pytest.raises(ValueError, match="schema_version"):
        compile_paper(paper, tmp_path / "bundle")


def test_compile_invalid_output_target(tmp_path):
    target = tmp_path / "file"
    target.write_text("x", encoding="utf-8")

    from src.question_compiler import compile_paper

    with pytest.raises(ValueError, match="not a directory"):
        compile_paper(load_paper(), target)


def test_verify_non_directory(tmp_path):
    target = tmp_path / "file"
    target.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="not a directory"):
        verify_compilation(str(target))


def test_verify_expected_hash_mismatch(tmp_path):
    out = tmp_path / "bundle"
    result = compile_paper(load_paper(), out, formats=("markdown",))

    with pytest.raises(ValueError, match="input identity"):
        verify_compilation(str(out), expected_input_sha256="0" * 64)

    assert result.success
