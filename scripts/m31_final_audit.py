from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    required = [
        "README.md",
        "requirements.txt",
        ".coveragerc",
        "src",
        "tests",
        "input",
        "output",
        ".github/workflows",
        "docs/milestones/M31/ACCEPTANCE.md",
        "docs/milestones/M31/RELEASE_NOTES.md",
        "tests/test_milestone31_final.py",
    ]

    missing = [p for p in required if not (ROOT / p).exists()]
    if missing:
        print("M31 required files missing:")
        for item in missing:
            print(item)
        return 1

    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()

    bad = [
        p for p in tracked
        if "/__pycache__/" in f"/{p}"
        or p.endswith((".pyc", ".pyo", ".pyd"))
        or p == ".coverage"
        or p.startswith("coverage/")
    ]

    if bad:
        print("M31 release cleanliness FAILED:")
        for item in bad:
            print(item)
        return 1

    print("=== M31 final certification audit ===")
    print("Repository structure: PASSED")
    print("Formatter v1.0 documentation: PASSED")
    print("Tracked generated-file audit: PASSED")
    print("Release cleanliness: PASSED")
    print("M31 FINAL CERTIFICATION AUDIT: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
