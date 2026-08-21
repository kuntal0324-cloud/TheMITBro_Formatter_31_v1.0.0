#!/usr/bin/env python3
"""Generate a deterministic M30 release-candidate source manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {".git", ".pytest_cache", "__pycache__", "coverage", "junit", ".venv", "venv"}
EXCLUDED_NAMES = {".coverage"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest() -> dict:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if path.name in EXCLUDED_NAMES:
            continue
        files.append({"path": rel.as_posix(), "sha256": sha256(path), "bytes": path.stat().st_size})

    return {
        "contract": "M30",
        "release_candidate": "1.0.0-rc.1",
        "api_version": "1.0",
        "build_contract": "26.0",
        "input_schema": "1.0",
        "file_count": len(files),
        "files": files,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    manifest = build_manifest()
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
