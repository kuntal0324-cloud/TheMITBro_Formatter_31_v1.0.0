#!/usr/bin/env python3
"""Create a deterministic SHA-256 manifest from Git-tracked release files."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

EXCLUDED_PREFIXES = (
    ".git/",
)

EXCLUDED_FILES = {
    ".coverage",
}


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    ).stdout.decode()
    return sorted(x for x in out.split("\0") if x)


def include(path: str) -> bool:
    if any(path.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    return path not in EXCLUDED_FILES


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="release/SHA256SUMS")
    args = parser.parse_args()

    files = [p for p in tracked_files() if include(p)]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for name in files:
        path = Path(name)
        if not path.is_file():
            raise SystemExit(f"Tracked file is missing from worktree: {name}")
        lines.append(f"{sha256(path)}  {name}")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Manifest entries: {len(lines)}")
    print(f"Manifest written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
