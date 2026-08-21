"""Independent Milestone 29 formatter completeness audit."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.math_normalizer import normalize_expression, validate_expression
from src.public_api import compile_paper, format_markdown, validate_markdown

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "input" / "milestone28_real_world_corpus.json"
REQUIRED = (
    "docs/milestones/M29/ACCEPTANCE.md",
    "docs/milestones/M29/RELEASE_NOTES.md",
    "tests/test_milestone29_completeness.py",
    "scripts/m29_completeness_audit.py",
    ".github/workflows/m29-completeness.yml",
)


def main() -> int:
    missing = [item for item in REQUIRED if not (ROOT / item).is_file()]
    if missing:
        raise SystemExit("M29 required files missing: " + ", ".join(missing))

    expected = {
        "\\operatorname{det}(A)": "\\mathrm{det}(A)",
        "π ≤ x": "\\pi  \\leq  x",
        "x¹": "x^1",
        "a ± b": "a \\pm  b",
        "x − y → z": "x - y \\to  z",
    }
    for source, target in expected.items():
        actual = normalize_expression(source)
        if actual != target:
            raise SystemExit(f"M29 normalization mismatch: {source!r} -> {actual!r}")

    if validate_expression(r"\\frac{a}{b").valid:
        raise SystemExit("M29 malformed-expression validation failed.")

    validation = validate_markdown("## Question\n\nFind $$\\frac{a}{b$$.\n")
    if validation.valid:
        raise SystemExit("M29 Markdown fail-closed validation failed.")

    normalized = format_markdown(
        "## Question\n\nEvaluate π × x² and use \\operatorname{det}(A).\n"
    )
    for token in ("\\pi", "\\times", "x^2", "\\mathrm{det}"):
        if token not in normalized:
            raise SystemExit(f"M29 formatter normalization missing: {token}")
    if "\\operatorname" in normalized or "−" in normalized:
        raise SystemExit("M29 formatter left legacy/unicode math markers behind.")

    papers = json.loads(CORPUS.read_text(encoding="utf-8"))["papers"]
    sample = papers[0]
    with tempfile.TemporaryDirectory(prefix="themitbro-m29-") as tmp:
        out = Path(tmp) / "paper"
        result = compile_paper(sample, out, formats=("markdown", "svg", "pdf", "html"))
        if not result.success:
            raise SystemExit("M29 representative compilation failed.")
        report = __import__("src.public_api", fromlist=["verify_compilation"]).verify_compilation(
            out, expected_input_sha256=result.input_sha256
        )
        if not report["valid"]:
            raise SystemExit("M29 representative artifact verification failed.")

    print("=== M29 formatter completeness audit ===")
    print("Required M29 files: PASSED")
    print("Mathematical Unicode normalization: PASSED")
    print("Legacy operator normalization: PASSED")
    print("Malformed-expression fail-closed validation: PASSED")
    print("Markdown structural validation: PASSED")
    print("Representative production compilation: PASSED")
    print("Artifact verification: PASSED")
    print("M29 completeness audit: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
