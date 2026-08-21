"""Milestone 25 end-to-end question-paper compilation pipeline.

M25 freezes a small application-facing contract around the existing M20/M21
production stack. It does not replace the renderers; it orchestrates them.

Input:
    A mapping accepted by ``PaperSpec.from_dict``.

Outputs:
    markdown  - normalized question-paper Markdown
    svg       - deterministic M20 SVG pages
    pdf       - deterministic M21 PDF
    html      - self-contained M21 HTML

The compiler is deliberately fail-closed: invalid paper data raises before
production files are emitted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping, Sequence

from .html_production import render_paper_html
from .pdf_production import render_paper_pdf
from .question_formatter import format_document
from .question_paper_ir import PaperSpec
from .question_paper_renderer import QuestionPaperRenderer


SUPPORTED_FORMATS = ("markdown", "svg", "pdf", "html")
COMPILER_VERSION = "25.0"
BUILD_CONTRACT_VERSION = "26.0"
INPUT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class CompilationArtifact:
    """One generated artifact with a stable relative name and SHA-256."""

    kind: str
    path: str
    sha256: str
    bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "path": self.path,
            "sha256": self.sha256,
            "bytes": self.bytes,
        }


@dataclass(frozen=True)
class CompilationResult:
    """Machine-readable M25 compilation result."""

    status: str
    compiler_version: str
    api_contract: str
    question_count: int
    page_count: int
    total_marks: float
    output_dir: str
    artifacts: tuple[CompilationArtifact, ...] = field(default_factory=tuple)
    input_sha256: str = ""
    build_contract: str = BUILD_CONTRACT_VERSION

    @property
    def success(self) -> bool:
        return self.status == "COMPILED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "compiler_version": self.compiler_version,
            "api_contract": self.api_contract,
            "question_count": self.question_count,
            "page_count": self.page_count,
            "total_marks": self.total_marks,
            "output_dir": self.output_dir,
            "input_sha256": self.input_sha256,
            "build_contract": self.build_contract,
            "artifacts": [item.to_dict() for item in self.artifacts],
        }


def canonicalize_paper_input(paper: Mapping[str, Any]) -> bytes:
    """Return the canonical JSON bytes used for M26 input identity.

    The representation is independent of mapping insertion order and uses
    UTF-8 without ASCII escaping. This is intentionally limited to JSON-like
    data because the compiler input contract is a structured paper document.
    """
    if not isinstance(paper, Mapping):
        raise TypeError("paper must be a mapping")
    payload = dict(paper)
    schema_version = str(payload.get("schema_version", INPUT_SCHEMA_VERSION))
    if schema_version != INPUT_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported paper schema_version: {schema_version}. "
            f"Supported: {INPUT_SCHEMA_VERSION}"
        )
    payload["schema_version"] = schema_version
    try:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TypeError("paper must contain JSON-serializable values") from exc


def input_sha256(paper: Mapping[str, Any]) -> str:
    """Return the SHA-256 identity of the canonical M26 paper input."""
    return hashlib.sha256(canonicalize_paper_input(paper)).hexdigest()


def verify_output_bundle(
    output_dir: str | Path,
    *,
    expected_input_sha256: str | None = None,
) -> dict[str, Any]:
    """Verify an M26 compilation bundle without regenerating it."""
    directory = Path(output_dir)
    if not directory.is_dir():
        raise ValueError(f"Output path is not a directory: {directory}")

    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("Compilation manifest is missing: manifest.json")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Compilation manifest is invalid JSON.") from exc

    required = {
        "compiler_version", "api_contract", "build_contract",
        "input_schema_version", "input_sha256", "deterministic",
        "question_count", "page_count", "total_marks", "artifact_count",
        "artifacts", "manifest_sha256",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ValueError(
            "Compilation manifest missing fields: " + ", ".join(missing)
        )

    manifest_hash = manifest.get("manifest_sha256")
    if (
        not isinstance(manifest_hash, str)
        or not re.fullmatch(r"[0-9a-f]{64}", manifest_hash)
    ):
        raise ValueError("Compilation manifest contains an invalid manifest SHA-256.")
    if manifest_hash != _manifest_sha256(manifest):
        raise ValueError("Compilation manifest hash mismatch.")

    if manifest["build_contract"] != BUILD_CONTRACT_VERSION:
        raise ValueError(
            f"Unsupported build contract: {manifest['build_contract']}. "
            f"Expected {BUILD_CONTRACT_VERSION}."
        )
    if manifest["input_schema_version"] != INPUT_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported input schema version: {manifest['input_schema_version']}."
        )
    if not manifest["deterministic"]:
        raise ValueError("Compilation manifest must declare deterministic=true.")

    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("Compilation manifest must contain at least one artifact.")
    if manifest.get("artifact_count") != len(artifacts):
        raise ValueError("Compilation manifest artifact_count is inconsistent.")

    checked: list[str] = []
    for item in artifacts:
        if not isinstance(item, dict):
            raise ValueError("Compilation manifest contains an invalid artifact entry.")
        path_value = item.get("path")
        if (
            not isinstance(path_value, str)
            or not path_value
            or Path(path_value).name != path_value
            or Path(path_value).is_absolute()
        ):
            raise ValueError(f"Invalid artifact path in manifest: {path_value!r}")
        path = directory / path_value
        if not path.is_file():
            raise ValueError(f"Missing artifact: {path_value}")
        actual_bytes = path.stat().st_size
        actual_hash = _sha256(path)
        if actual_bytes != int(item.get("bytes", -1)):
            raise ValueError(f"Artifact byte count mismatch: {path_value}")
        if actual_hash != item.get("sha256"):
            raise ValueError(f"Artifact hash mismatch: {path_value}")
        checked.append(path_value)

    if len(set(checked)) != len(checked):
        raise ValueError("Compilation manifest contains duplicate artifact paths.")

    expected_paths = set(checked) | {"manifest.json"}
    actual_paths = {item.name for item in directory.iterdir() if item.is_file()}
    if actual_paths != expected_paths:
        raise ValueError(
            "Compilation output contains unexpected or missing files: "
            f"expected={sorted(expected_paths)}, actual={sorted(actual_paths)}"
        )

    canonical_manifest = json.dumps(
        manifest,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"
    if manifest_path.read_text(encoding="utf-8") != canonical_manifest:
        raise ValueError("Compilation manifest is not canonically serialized.")

    input_hash = str(manifest["input_sha256"])
    if not re.fullmatch(r"[0-9a-f]{64}", input_hash):
        raise ValueError("Compilation manifest contains an invalid input SHA-256.")
    if expected_input_sha256 is not None and input_hash != expected_input_sha256:
        raise ValueError("Compilation input identity does not match the expected SHA-256.")

    return {
        "valid": True,
        "build_contract": manifest["build_contract"],
        "input_sha256": input_hash,
        "artifact_count": len(artifacts),
        "checked_artifacts": tuple(sorted(checked)),
    }


def _validate_formats(formats: Sequence[str]) -> tuple[str, ...]:
    if isinstance(formats, (str, bytes)):
        raise TypeError("formats must be a sequence such as ('markdown', 'pdf')")
    normalized = tuple(str(item).lower().strip() for item in formats)
    if not normalized:
        raise ValueError("At least one output format must be requested.")
    if len(normalized) != len(set(normalized)):
        raise ValueError("Output formats must be unique.")
    unknown = sorted(set(normalized) - set(SUPPORTED_FORMATS))
    if unknown:
        raise ValueError(
            f"Unsupported output format(s): {', '.join(unknown)}. "
            f"Supported: {', '.join(SUPPORTED_FORMATS)}"
        )
    return normalized


def _paper_markdown(paper: PaperSpec) -> str:
    """Serialize a PaperSpec to deterministic, human-readable Markdown."""
    lines = [f"# {paper.title}"]
    metadata = [
        ("Exam", paper.exam),
        ("Subject", paper.subject),
        ("Duration", f"{paper.duration_minutes} minutes" if paper.duration_minutes else None),
        ("Total Marks", f"{paper.resolved_total_marks():g}"),
    ]
    for label, value in metadata:
        if value is not None and str(value).strip():
            lines.append(f"**{label}:** {value}")

    if paper.instructions:
        lines.append("")
        lines.append("## Instructions")
        for instruction in paper.instructions:
            lines.append(f"- {format_document(str(instruction)).strip()}")

    lines.append("")
    lines.append("## Questions")

    for index, question in enumerate(paper.questions, start=1):
        number = question.number if question.number is not None else index
        mark = f" **[{question.marks:g} marks]**" if question.marks is not None else ""
        lines.append("")
        lines.append(f"### {number}.{mark}")
        if question.section:
            lines.append(f"**Section:** {question.section}")
        lines.append(format_document(question.text).strip())

        if question.options:
            for option_index, option in enumerate(question.options):
                label = chr(ord("A") + option_index) if option_index < 26 else str(option_index + 1)
                lines.append(f"{label}. {format_document(str(option)).strip()}")

        if question.diagrams:
            for diagram in question.diagrams:
                title = diagram.title or diagram.diagram_type
                lines.append(f"_Diagram: {title}_")

    return "\n".join(lines).strip() + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_sha256(payload: Mapping[str, Any]) -> str:
    """Hash the canonical manifest payload excluding its self-hash field."""
    unsigned = dict(payload)
    unsigned.pop("manifest_sha256", None)
    canonical = json.dumps(
        unsigned,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb", dir=str(path.parent), prefix=f".{path.name}.", delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(data)
    temporary.replace(path)


def _write_text_atomic(path: Path, text: str) -> None:
    _write_atomic(path, text.encode("utf-8"))


def _generate_to_staging(
    paper: PaperSpec,
    staging: Path,
    formats: tuple[str, ...],
    input_hash: str,
) -> tuple[list[CompilationArtifact], int]:
    staging.mkdir(parents=True, exist_ok=True)
    renderer = QuestionPaperRenderer()
    rendered = renderer.render(paper)

    artifacts: list[CompilationArtifact] = []

    if "markdown" in formats:
        path = staging / "paper.md"
        _write_text_atomic(path, _paper_markdown(paper))
        artifacts.append(
            CompilationArtifact("markdown", "paper.md", _sha256(path), path.stat().st_size)
        )

    if "svg" in formats:
        path = staging / "paper.svg"
        _write_text_atomic(path, rendered.svg)
        artifacts.append(
            CompilationArtifact("svg", "paper.svg", _sha256(path), path.stat().st_size)
        )

    if "pdf" in formats:
        path = staging / "paper.pdf"
        render_paper_pdf(paper, path)
        artifacts.append(
            CompilationArtifact("pdf", "paper.pdf", _sha256(path), path.stat().st_size)
        )

    if "html" in formats:
        path = staging / "paper.html"
        render_paper_html(paper, path)
        artifacts.append(
            CompilationArtifact("html", "paper.html", _sha256(path), path.stat().st_size)
        )

    # Manifest is part of the compiler contract whenever any production output
    # is requested. It makes the exact generated set independently auditable.
    manifest_path = staging / "manifest.json"
    manifest_payload = {
        "compiler_version": COMPILER_VERSION,
        "api_contract": "1.0",
        "build_contract": BUILD_CONTRACT_VERSION,
        "input_schema_version": INPUT_SCHEMA_VERSION,
        "input_sha256": input_hash,
        "deterministic": True,
        "question_count": len(paper.questions),
        "page_count": len(rendered.pages),
        "total_marks": paper.resolved_total_marks(),
        "artifact_count": len(artifacts),
        "artifacts": [
            {"kind": item.kind, "path": item.path, "sha256": item.sha256, "bytes": item.bytes}
            for item in sorted(artifacts, key=lambda item: item.path)
        ],
    }
    manifest_payload["manifest_sha256"] = _manifest_sha256(manifest_payload)
    _write_text_atomic(
        manifest_path,
        json.dumps(
            manifest_payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ) + "\n",
    )
    artifacts.append(
        CompilationArtifact(
            "manifest",
            "manifest.json",
            _sha256(manifest_path),
            manifest_path.stat().st_size,
        )
    )

    return artifacts, len(rendered.pages)


def compile_paper(
    paper: Mapping[str, Any],
    output_dir: str | Path,
    *,
    formats: Sequence[str] = SUPPORTED_FORMATS,
) -> CompilationResult:
    """Compile a paper into a clean output directory.

    Generation happens in a staging directory first. Existing output is
    replaced only after every requested artifact is successfully generated.
    """
    if not isinstance(paper, Mapping):
        raise TypeError("paper must be a mapping")

    selected = _validate_formats(formats)
    input_hash = input_sha256(paper)

    payload = dict(paper)
    schema_version = str(payload.pop("schema_version", INPUT_SCHEMA_VERSION))
    if schema_version != INPUT_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported paper schema_version: {schema_version}. "
            f"Supported: {INPUT_SCHEMA_VERSION}"
        )

    paper_spec = PaperSpec.from_dict(payload)
    paper_spec.ensure_valid()

    destination = Path(output_dir)
    if destination.exists() and not destination.is_dir():
        raise ValueError(f"Output path is not a directory: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=".themitbro-m25-", dir=str(destination.parent)
    ) as temporary:
        staging = Path(temporary)
        artifacts, page_count = _generate_to_staging(
            paper_spec, staging, selected, input_hash
        )

        if destination.exists():
            for child in destination.iterdir():
                if child.is_dir():
                    import shutil
                    shutil.rmtree(child)
                else:
                    child.unlink()

        destination.mkdir(parents=True, exist_ok=True)
        for item in artifacts:
            source = staging / item.path
            target = destination / item.path
            target.parent.mkdir(parents=True, exist_ok=True)
            source.replace(target)

    # Recalculate hashes after staging move; bytes are unchanged.
    final_artifacts = tuple(
        CompilationArtifact(
            item.kind,
            item.path,
            _sha256(destination / item.path),
            (destination / item.path).stat().st_size,
        )
        for item in sorted(artifacts, key=lambda x: x.path)
    )

    return CompilationResult(
        status="COMPILED",
        compiler_version=COMPILER_VERSION,
        api_contract="1.0",
        question_count=len(paper_spec.questions),
        page_count=page_count,
        total_marks=paper_spec.resolved_total_marks(),
        output_dir=str(destination),
        artifacts=final_artifacts,
        input_sha256=input_hash,
        build_contract=BUILD_CONTRACT_VERSION,
    )


__all__ = [
    "BUILD_CONTRACT_VERSION",
    "COMPILER_VERSION",
    "INPUT_SCHEMA_VERSION",
    "SUPPORTED_FORMATS",
    "canonicalize_paper_input",
    "input_sha256",
    "verify_output_bundle",
    "CompilationArtifact",
    "CompilationResult",
    "compile_paper",
]
