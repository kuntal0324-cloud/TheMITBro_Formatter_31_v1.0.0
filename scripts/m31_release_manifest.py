from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "milestone31_release_manifest.json"

FILES = [
    "README.md",
    "requirements.txt",
    ".coveragerc",
    "docs/milestones/M31/ACCEPTANCE.md",
    "docs/milestones/M31/RELEASE_NOTES.md",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "release": "1.0.0",
        "status": "stable",
        "milestone": "M31",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": {
            p: sha256(ROOT / p)
            for p in FILES
            if (ROOT / p).is_file()
        },
    }
    OUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
