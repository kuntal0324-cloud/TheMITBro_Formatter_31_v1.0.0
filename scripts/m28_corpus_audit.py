"""Independent Milestone 28 real-world corpus audit."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from src.public_api import compile_paper, verify_compilation

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "input" / "milestone28_real_world_corpus.json"
REQUIRED = (
    "docs/milestones/M28/ACCEPTANCE.md",
    "docs/milestones/M28/RELEASE_NOTES.md",
    "tests/test_milestone28_corpus.py",
    "scripts/m28_corpus_audit.py",
    ".github/workflows/m28-corpus.yml",
    "input/milestone28_real_world_corpus.json",
)


def main() -> int:
    missing=[p for p in REQUIRED if not (ROOT/p).is_file()]
    if missing:
        raise SystemExit("M28 required files missing: "+", ".join(missing))
    data=json.loads(CORPUS.read_text(encoding="utf-8"))
    if data.get("contract") != "M28" or data.get("version") != "28.0":
        raise SystemExit("M28 corpus contract/version invalid.")
    papers=data.get("papers")
    if not isinstance(papers,list) or len(papers)!=20:
        raise SystemExit("M28 corpus must contain exactly 20 papers.")
    ids=[p["metadata"]["case_id"] for p in papers]
    families=[p["metadata"]["family"] for p in papers]
    if len(set(ids))!=20 or len(set(families))!=20:
        raise SystemExit("M28 corpus IDs/families must be unique.")
    with tempfile.TemporaryDirectory(prefix="themitbro-m28-") as tmp:
        root=Path(tmp)
        for paper in papers:
            case=paper["metadata"]["case_id"]
            a=root/(case+"-a"); b=root/(case+"-b")
            ra=compile_paper(paper,a)
            rb=compile_paper(paper,b)
            if not ra.success or not rb.success:
                raise SystemExit(f"M28 compilation failed: {case}")
            va=verify_compilation(a,expected_input_sha256=ra.input_sha256)
            vb=verify_compilation(b,expected_input_sha256=rb.input_sha256)
            if not va["valid"] or not vb["valid"]:
                raise SystemExit(f"M28 artifact verification failed: {case}")
            names=("paper.md","paper.svg","paper.pdf","paper.html","manifest.json")
            for name in names:
                if (a/name).read_bytes() != (b/name).read_bytes():
                    raise SystemExit(f"M28 nondeterministic artifact: {case}/{name}")
    print("=== M28 real-world corpus audit ===")
    print("Corpus size (20 papers): PASSED")
    print("Family diversity (20 families): PASSED")
    print("All-format compilation: PASSED")
    print("Artifact verification: PASSED")
    print("Deterministic output: PASSED")
    print("M28 corpus audit: PASSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
