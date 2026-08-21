#!/usr/bin/env python3
"""Milestone 26 reproducible-build and artifact-integrity audit."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "input" / "milestone25_e2e_paper.json"

REQUIRED = (
    "src/public_api.py",
    "src/question_compiler.py",
    "tests/test_milestone26_integrity.py",
    "input/milestone25_e2e_paper.json",
    "docs/milestones/M26/ACCEPTANCE.md",
    "docs/milestones/M26/RELEASE_NOTES.md",
    ".github/workflows/m26-integrity.yml",
)


def audit_structure() -> None:
    missing = [item for item in REQUIRED if not (ROOT / item).is_file()]
    if missing:
        raise SystemExit("M26 required files missing: " + ", ".join(missing))


def audit_contract() -> None:
    sys.path.insert(0, str(ROOT))
    from src.public_api import (
        API_VERSION,
        BUILD_CONTRACT_VERSION,
        INPUT_SCHEMA_VERSION,
        get_input_sha256,
        verify_compilation,
        compile_paper,
    )

    if API_VERSION != "1.0":
        raise SystemExit("Unexpected public API version.")
    if BUILD_CONTRACT_VERSION != "26.0":
        raise SystemExit("Unexpected M26 build contract version.")
    if INPUT_SCHEMA_VERSION != "1.0":
        raise SystemExit("Unexpected input schema version.")

    paper = json.loads(FIXTURE.read_text(encoding="utf-8"))
    identity = get_input_sha256(paper)

    with tempfile.TemporaryDirectory(prefix="themitbro-m26-audit-") as tmp:
        out = Path(tmp) / "bundle"
        result = compile_paper(paper, out)
        report = verify_compilation(
            out,
            expected_input_sha256=identity,
        )

        if not result.success:
            raise SystemExit("M26 compilation did not succeed.")
        if result.build_contract != "26.0":
            raise SystemExit("M26 result has an invalid build contract.")
        if result.input_sha256 != identity:
            raise SystemExit("M26 input identity mismatch.")
        if not report["valid"] or report["artifact_count"] != 4:
            raise SystemExit("M26 bundle verification failed.")

        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        if manifest["input_sha256"] != identity:
            raise SystemExit("M26 manifest input hash mismatch.")
        if manifest["artifact_count"] != 4:
            raise SystemExit("M26 manifest artifact count mismatch.")


def main() -> int:
    audit_structure()
    audit_contract()
    print("=== M26 reproducible-build audit ===")
    print("Required structure: PASSED")
    print("Build contract: PASSED")
    print("Canonical input identity: PASSED")
    print("Artifact verification: PASSED")
    print("M26 integrity audit: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
