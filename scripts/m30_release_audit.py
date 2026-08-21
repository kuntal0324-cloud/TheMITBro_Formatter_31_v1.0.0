#!/usr/bin/env python3
"""Independent M30 release-candidate audit."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from src.public_api import API_VERSION, BUILD_CONTRACT_VERSION, INPUT_SCHEMA_VERSION
from src.public_api import compile_paper, get_input_sha256, verify_compilation

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "input" / "milestone28_real_world_corpus.json"

REQUIRED = (
    "README.md",
    "docs/ROADMAP.md",
    "docs/ARCHITECTURE.md",
    "docs/FORMAT_SPECIFICATION.md",
    "docs/RELEASE_PROCESS.md",
    "docs/milestones/README.md",
    "docs/milestones/M30/ACCEPTANCE.md",
    "docs/milestones/M30/RELEASE_NOTES.md",
    "tests/test_milestone30_release_candidate.py",
    "scripts/m30_release_manifest.py",
    "scripts/m30_release_audit.py",
    ".github/workflows/m30-release-candidate.yml",
)


def audit_structure() -> None:
    missing = [item for item in REQUIRED if not (ROOT / item).is_file()]
    if missing:
        raise SystemExit("M30 required files missing: " + ", ".join(missing))

    legacy = [
        p.name for p in ROOT.iterdir()
        if p.is_file() and (
            (p.name.startswith("MILESTONE") and p.name.endswith(("_ACCEPTANCE.md", "_RELEASE_NOTES.md")))
            or p.name == "README_MILESTONE20.md"
        )
    ]
    if legacy:
        raise SystemExit("Legacy milestone documents remain in root: " + ", ".join(sorted(legacy)))


def audit_contract() -> None:
    if API_VERSION != "1.0":
        raise SystemExit(f"Unexpected API version: {API_VERSION}")
    if BUILD_CONTRACT_VERSION != "26.0":
        raise SystemExit(f"Unexpected build contract: {BUILD_CONTRACT_VERSION}")
    if INPUT_SCHEMA_VERSION != "1.0":
        raise SystemExit(f"Unexpected input schema: {INPUT_SCHEMA_VERSION}")


def audit_production_candidate() -> None:
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    papers = data.get("papers")
    if not isinstance(papers, list) or not papers:
        raise SystemExit("M28 real-world corpus is unavailable or empty.")

    paper = papers[0]
    identity = get_input_sha256(paper)
    with tempfile.TemporaryDirectory(prefix="themitbro-m30-audit-") as tmp:
        root = Path(tmp)
        first = root / "first"
        second = root / "second"
        a = compile_paper(paper, first, formats=("markdown", "svg", "pdf", "html"))
        b = compile_paper(paper, second, formats=("markdown", "svg", "pdf", "html"))
        if not a.success or not b.success:
            raise SystemExit("M30 representative compilation failed.")
        if a.input_sha256 != identity or b.input_sha256 != identity:
            raise SystemExit("M30 input identity mismatch.")
        if not verify_compilation(first, expected_input_sha256=identity)["valid"]:
            raise SystemExit("M30 first artifact bundle verification failed.")
        if not verify_compilation(second, expected_input_sha256=identity)["valid"]:
            raise SystemExit("M30 second artifact bundle verification failed.")
        for name in ("paper.md", "paper.svg", "paper.pdf", "paper.html", "manifest.json"):
            if (first / name).read_bytes() != (second / name).read_bytes():
                raise SystemExit(f"M30 nondeterministic artifact: {name}")


def audit_git_cleanliness() -> None:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True)
    tracked = result.stdout.splitlines()
    forbidden = [
        p for p in tracked
        if "/__pycache__/" in f"/{p}/"
        or p.endswith((".pyc", ".pyo", ".pyd"))
        or p == ".coverage"
        or p.startswith("coverage/")
        or p.startswith(".pytest_cache/")
    ]
    if forbidden:
        raise SystemExit("Generated files are tracked: " + ", ".join(forbidden))


def main() -> int:
    audit_structure()
    audit_contract()
    audit_production_candidate()
    audit_git_cleanliness()
    print("=== M30 release-candidate audit ===")
    print("Documentation structure: PASSED")
    print("Root milestone-document cleanup: PASSED")
    print("Public API/build contract: PASSED")
    print("Representative production compilation: PASSED")
    print("Deterministic artifacts: PASSED")
    print("Release cleanliness: PASSED")
    print("M30 release-candidate audit: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
