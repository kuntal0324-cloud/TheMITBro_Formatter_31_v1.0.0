from pathlib import Path
import hashlib
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_m31_documentation_exists():
    assert (ROOT / "docs/milestones/M31/ACCEPTANCE.md").is_file()
    assert (ROOT / "docs/milestones/M31/RELEASE_NOTES.md").is_file()


def test_repository_has_required_core_structure():
    for name in ("src", "tests", "input", "output", ".github/workflows"):
        assert (ROOT / name).exists()
    for name in ("README.md", "requirements.txt", ".coveragerc"):
        assert (ROOT / name).is_file()


def test_no_tracked_python_cache_files():
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    bad = [
        line for line in result.stdout.splitlines()
        if "/__pycache__/" in f"/{line}" or
           line.endswith((".pyc", ".pyo", ".pyd"))
    ]
    assert not bad, bad


def test_release_notes_identify_v1():
    text = (ROOT / "docs/milestones/M31/RELEASE_NOTES.md").read_text()
    assert "v1.0.0" in text
    assert "stable" in text


def test_source_compiles():
    result = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "src"],
        cwd=ROOT,
    )
    assert result.returncode == 0
