"""Independent Milestone 27 quality audit.

The audit intentionally exercises the public API and production artifacts rather
than importing renderer implementation details.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from src.public_api import (
    API_VERSION,
    BUILD_CONTRACT_VERSION,
    INPUT_SCHEMA_VERSION,
    compile_paper,
    get_input_sha256,
    verify_compilation,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "input" / "milestone27_quality_corpus.json"


REQUIRED = (
    "docs/milestones/M27/ACCEPTANCE.md",
    "docs/milestones/M27/RELEASE_NOTES.md",
    "tests/test_milestone27_quality.py",
    "scripts/m27_quality_audit.py",
    ".github/workflows/m27-quality.yml",
    "input/milestone27_quality_corpus.json",
)


def audit_required_files() -> None:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit("M27 required files missing: " + ", ".join(missing))


def load_corpus() -> list[dict]:
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    if data.get("contract") != "M27":
        raise SystemExit("M27 corpus contract marker is invalid.")
    papers = data.get("papers")
    if not isinstance(papers, list) or not papers:
        raise SystemExit("M27 quality corpus is empty.")
    return papers


def audit_api() -> None:
    if API_VERSION != "1.0":
        raise SystemExit(f"Unexpected API version: {API_VERSION}")
    if BUILD_CONTRACT_VERSION != "26.0":
        raise SystemExit(f"Unexpected build contract: {BUILD_CONTRACT_VERSION}")
    if INPUT_SCHEMA_VERSION != "1.0":
        raise SystemExit(f"Unexpected input schema: {INPUT_SCHEMA_VERSION}")


def audit_paper(paper: dict, root: Path) -> None:
    case_id = paper.get("metadata", {}).get("case_id", "unknown")
    first = root / f"{case_id}-a"
    second = root / f"{case_id}-b"

    result_a = compile_paper(
        paper, first, formats=("markdown", "svg", "pdf", "html")
    )
    result_b = compile_paper(
        paper, second, formats=("markdown", "svg", "pdf", "html")
    )

    if not result_a.success or not result_b.success:
        raise SystemExit(f"M27 compilation failed for {case_id}")

    if result_a.input_sha256 != get_input_sha256(paper):
        raise SystemExit(f"M27 input identity mismatch for {case_id}")

    verify_compilation(first, expected_input_sha256=result_a.input_sha256)
    verify_compilation(second, expected_input_sha256=result_b.input_sha256)

    names = ("paper.md", "paper.svg", "paper.pdf", "paper.html", "manifest.json")
    for name in names:
        left = (first / name).read_bytes()
        right = (second / name).read_bytes()
        if left != right:
            raise SystemExit(f"M27 nondeterministic artifact: {case_id}/{name}")

    svg = (first / "paper.svg").read_text(encoding="utf-8")
    if not svg.startswith("<svg ") or "NaN" in svg or "undefined" in svg:
        raise SystemExit(f"M27 SVG quality failure: {case_id}")

    html = (first / "paper.html").read_text(encoding="utf-8").lower()
    if "<html" not in html or "</html>" not in html or "undefined" in html:
        raise SystemExit(f"M27 HTML quality failure: {case_id}")

    if not (first / "paper.pdf").read_bytes().startswith(b"%PDF"):
        raise SystemExit(f"M27 PDF quality failure: {case_id}")

    markdown = (first / "paper.md").read_text(encoding="utf-8")
    if not markdown.startswith("# ") or "## Questions" not in markdown:
        raise SystemExit(f"M27 Markdown quality failure: {case_id}")

    print(f"{case_id}: END-TO-END + DETERMINISM + ARTIFACTS PASSED")


def main() -> int:
    audit_required_files()
    audit_api()

    with tempfile.TemporaryDirectory(prefix="themitbro-m27-") as tmp:
        root = Path(tmp)
        for paper in load_corpus():
            audit_paper(paper, root)

    print("=== M27 quality audit ===")
    print("Required structure: PASSED")
    print("Public API contract: PASSED")
    print("Representative corpus: PASSED")
    print("End-to-end production: PASSED")
    print("Deterministic artifacts: PASSED")
    print("Artifact sanity: PASSED")
    print("M27 quality audit: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
