from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.public_api import API_VERSION, BUILD_CONTRACT_VERSION, INPUT_SCHEMA_VERSION
from src.public_api import compile_paper, get_input_sha256, verify_compilation

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "input" / "milestone28_real_world_corpus.json"


def test_m30_documentation_structure():
    required = [
        "README.md",
        "docs/ROADMAP.md",
        "docs/ARCHITECTURE.md",
        "docs/FORMAT_SPECIFICATION.md",
        "docs/RELEASE_PROCESS.md",
        "docs/milestones/README.md",
        "docs/milestones/M29/ACCEPTANCE.md",
        "docs/milestones/M29/RELEASE_NOTES.md",
        "docs/milestones/M30/ACCEPTANCE.md",
        "docs/milestones/M30/RELEASE_NOTES.md",
        ".github/workflows/m30-release-candidate.yml",
    ]
    missing = [item for item in required if not (ROOT / item).is_file()]
    assert not missing, f"M30 documentation/release files missing: {missing}"


def test_m30_root_is_free_of_legacy_milestone_documents():
    legacy = sorted(
        p.name
        for p in ROOT.iterdir()
        if p.is_file()
        and (
            p.name.startswith("MILESTONE")
            and (p.name.endswith("_ACCEPTANCE.md") or p.name.endswith("_RELEASE_NOTES.md"))
            or p.name == "README_MILESTONE20.md"
        )
    )
    assert not legacy, f"Legacy milestone documents remain in repository root: {legacy}"


def test_m30_contract_versions_remain_frozen():
    assert API_VERSION == "1.0"
    assert BUILD_CONTRACT_VERSION == "26.0"
    assert INPUT_SCHEMA_VERSION == "1.0"


def test_m30_representative_production_build_is_deterministic():
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    paper = data["papers"][0]
    identity = get_input_sha256(paper)

    with tempfile.TemporaryDirectory(prefix="themitbro-m30-") as tmp:
        root = Path(tmp)
        first = root / "first"
        second = root / "second"

        a = compile_paper(paper, first, formats=("markdown", "svg", "pdf", "html"))
        b = compile_paper(paper, second, formats=("markdown", "svg", "pdf", "html"))

        assert a.success, a.message
        assert b.success, b.message
        assert a.input_sha256 == identity
        assert b.input_sha256 == identity

        assert verify_compilation(first, expected_input_sha256=identity)["valid"]
        assert verify_compilation(second, expected_input_sha256=identity)["valid"]

        names = ("paper.md", "paper.svg", "paper.pdf", "paper.html", "manifest.json")
        for name in names:
            assert (first / name).read_bytes() == (second / name).read_bytes(), name


def test_m30_manifest_generator_exists():
    assert (ROOT / "scripts/m30_release_manifest.py").is_file()
