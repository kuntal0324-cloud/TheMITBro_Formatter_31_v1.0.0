#!/usr/bin/env python3
"""Milestone 25 contract audit.

Checks the public API surface and executes the repository's canonical
end-to-end paper fixture. This is a release/CI audit, not a replacement for
pytest.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "input" / "milestone25_e2e_paper.json"

REQUIRED = (
    "src/public_api.py",
    "src/question_compiler.py",
    "tests/test_milestone25_release.py",
    "input/milestone25_e2e_paper.json",
    "docs/milestones/M25/ACCEPTANCE.md",
    "docs/milestones/M25/RELEASE_NOTES.md",
    ".github/workflows/m25-contract.yml",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_structure() -> None:
    missing = [item for item in REQUIRED if not (ROOT / item).is_file()]
    if missing:
        raise SystemExit("M25 required files missing: " + ", ".join(missing))


def audit_public_api() -> None:
    sys.path.insert(0, str(ROOT))
    from src.public_api import API_VERSION, format_markdown, validate_markdown
    from src.question_compiler import COMPILER_VERSION, SUPPORTED_FORMATS

    assert API_VERSION == "1.0"
    assert COMPILER_VERSION == "25.0"
    assert SUPPORTED_FORMATS == ("markdown", "svg", "pdf", "html")

    text = r"For A, use $\operatorname{det}(A)=1$."
    formatted = format_markdown(text)
    if r"\operatorname" in formatted:
        raise SystemExit("M25 API failed operator normalization.")

    if not validate_markdown(formatted).valid:
        raise SystemExit("M25 API validation failed.")


def audit_e2e() -> None:
    from src.public_api import compile_paper

    paper = json.loads(FIXTURE.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="themitbro-m25-audit-") as tmp:
        out = Path(tmp)
        result = compile_paper(paper, out)

        expected = {"paper.md", "paper.svg", "paper.pdf", "paper.html", "manifest.json"}
        actual = {path.name for path in out.iterdir()}

        if actual != expected:
            raise SystemExit(
                f"Unexpected M25 artifact set: {sorted(actual)}"
            )

        if result.status != "COMPILED" or result.question_count != 12:
            raise SystemExit("M25 end-to-end compilation returned invalid metadata.")

        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        for item in manifest["artifacts"]:
            path = out / item["path"]
            if sha256(path) != item["sha256"]:
                raise SystemExit(f"Manifest hash mismatch: {item['path']}")

        if not (out / "paper.pdf").read_bytes().startswith(b"%PDF-"):
            raise SystemExit("M25 PDF artifact is invalid.")

        html = (out / "paper.html").read_text(encoding="utf-8")
        if "<svg " not in html or "<!doctype html>" not in html.lower():
            raise SystemExit("M25 HTML artifact is invalid.")

        svg = (out / "paper.svg").read_text(encoding="utf-8")
        if not svg.startswith("<svg ") or "NaN" in svg or "undefined" in svg:
            raise SystemExit("M25 SVG artifact is invalid.")


def main() -> int:
    audit_structure()
    audit_public_api()
    audit_e2e()
    print("=== M25 contract audit ===")
    print("Required structure: PASSED")
    print("Public API contract: PASSED")
    print("End-to-end compiler: PASSED")
    print("Artifact integrity: PASSED")
    print("M25 contract audit: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
