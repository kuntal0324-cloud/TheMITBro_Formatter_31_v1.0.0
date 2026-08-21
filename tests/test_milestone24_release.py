from pathlib import Path
import re
import subprocess


def git_files():
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [x for x in result.stdout.decode().split("\0") if x]


def test_release_audit_script_exists():
    assert Path("scripts/m24_release_audit.py").is_file()


def test_manifest_script_exists():
    assert Path("scripts/m24_manifest.py").is_file()


def test_required_release_document_exists():
    assert Path("docs/milestones/M24/ACCEPTANCE.md").is_file()


def test_no_tracked_generated_files():
    forbidden = re.compile(
        r"(^|/)(__pycache__|\.pytest_cache)(/|$)|"
        r"(^|/).+\.py[cod]$|"
        r"(^|/)\.coverage$|"
        r"(^|/)coverage(/|$)"
    )
    bad = [name for name in git_files() if forbidden.search(name)]
    assert not bad, f"Forbidden tracked files: {bad}"


def test_no_tracked_env_files():
    bad = [
        name for name in git_files()
        if Path(name).name == ".env"
        or Path(name).name.startswith(".env.")
    ]
    assert not bad, f"Tracked environment files: {bad}"


def test_release_structure():
    files = set(git_files())
    assert "README.md" in files
    assert "requirements.txt" in files
    assert any(x.startswith("tests/") for x in files)
    assert any(x.startswith(".github/workflows/") for x in files)
