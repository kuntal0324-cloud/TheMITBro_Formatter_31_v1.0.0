#!/usr/bin/env python3
"""Milestone 24 release audit.

The audit intentionally works from Git's tracked file list so generated
working-tree files cannot accidentally become part of a release.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN_TRACKED = (
    re.compile(r"(^|/)(__pycache__)(/|$)"),
    re.compile(r"(^|/).+\.py[cod]$"),
    re.compile(r"(^|/)\.coverage$"),
    re.compile(r"(^|/)coverage(/|$)"),
    re.compile(r"(^|/)\.pytest_cache(/|$)"),
    re.compile(r"(^|/)\.env(?:\..*)?$"),
)

PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
)

REQUIRED = (
    "README.md",
    "requirements.txt",
    "tests/",
    ".github/workflows/",
)

EXCLUDED_MANIFEST_PREFIXES = (
    ".git/",
    ".github/",
)

EXCLUDED_MANIFEST_FILES = {
    ".coverage",
    "coverage.xml",
    "requirements-lock.txt",
}


def git_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [x for x in result.stdout.decode().split("\0") if x]


def current_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def audit(files: list[str]) -> list[str]:
    failures: list[str] = []

    for name in files:
        if any(p.search(name) for p in FORBIDDEN_TRACKED):
            failures.append(f"FORBIDDEN TRACKED FILE: {name}")

        path = Path(name)
        if path.is_file():
            try:
                data = path.read_bytes()
            except OSError as exc:
                failures.append(f"UNREADABLE FILE: {name}: {exc}")
                continue

            if PRIVATE_KEY_PATTERN.search(data.decode("utf-8", errors="ignore")):
                failures.append(f"PRIVATE KEY MATERIAL DETECTED: {name}")

    for required in REQUIRED:
        if required.endswith("/"):
            if not any(f.startswith(required) for f in files):
                failures.append(f"REQUIRED PATH MISSING: {required}")
        elif required not in files:
            failures.append(f"REQUIRED FILE MISSING: {required}")

    return failures


def main() -> int:
    files = git_files()
    failures = audit(files)

    print("=== M24 release audit ===")
    print(f"Tracked files: {len(files)}")
    print(f"Commit: {current_commit()}")

    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        print("M24 release audit: FAILED")
        return 1

    print("No forbidden generated files are tracked.")
    print("No obvious private-key material found in tracked files.")
    print("Required release structure is present.")
    print("M24 release audit: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
