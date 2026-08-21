"""TheMITbro Formatter public API contract (M25).

This module is intentionally small and stable. Applications should import from
here instead of depending on internal renderer/processor implementation details.

Contract:
    API_VERSION is the public contract version.
    format_markdown(text) -> str
    validate_markdown(text) -> ValidationResult
    compile_paper(data, output_dir, formats=...) -> CompilationResult
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .question_compiler import (
    BUILD_CONTRACT_VERSION,
    COMPILER_VERSION,
    INPUT_SCHEMA_VERSION,
    CompilationResult,
    compile_paper as _compile_paper,
    input_sha256 as _input_sha256,
    verify_output_bundle as _verify_output_bundle,
)
from .question_formatter import format_document
from .render_validator import validate_rendered_markdown

API_VERSION = "1.0"


@dataclass(frozen=True)
class ValidationResult:
    """Stable validation response exposed by the public API."""

    valid: bool
    checks: tuple[dict[str, Any], ...]
    formatted: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "checks": [dict(item) for item in self.checks],
            "formatted": self.formatted,
        }


def format_markdown(text: str) -> str:
    """Format one Markdown document using the frozen formatter contract."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return format_document(text)


def validate_markdown(text: str) -> ValidationResult:
    """Format and structurally validate one Markdown document."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    checks = validate_rendered_markdown(text)
    return ValidationResult(
        valid=all(check.passed for check in checks),
        checks=tuple(
            {
                "name": check.name,
                "passed": check.passed,
                "message": check.message,
            }
            for check in checks
        ),
        formatted=format_document(text),
    )


def compile_paper(
    paper: Mapping[str, Any],
    output_dir: str,
    *,
    formats: Sequence[str] = ("markdown", "svg", "pdf", "html"),
) -> CompilationResult:
    """Compile one structured question paper end-to-end.

    The input mapping follows ``PaperSpec.from_dict``. The function returns a
    structured result and writes only the requested production artifacts.
    """
    if not isinstance(paper, Mapping):
        raise TypeError("paper must be a mapping")
    return _compile_paper(paper, output_dir, formats=formats)


def get_input_sha256(paper: Mapping[str, Any]) -> str:
    """Return the canonical M26 identity hash for a structured paper input."""
    if not isinstance(paper, Mapping):
        raise TypeError("paper must be a mapping")
    return _input_sha256(paper)


def verify_compilation(
    output_dir: str,
    *,
    expected_input_sha256: str | None = None,
) -> dict[str, Any]:
    """Verify an M26 compilation bundle without modifying it."""
    return _verify_output_bundle(
        output_dir,
        expected_input_sha256=expected_input_sha256,
    )


__all__ = [
    "API_VERSION",
    "BUILD_CONTRACT_VERSION",
    "COMPILER_VERSION",
    "INPUT_SCHEMA_VERSION",
    "CompilationResult",
    "ValidationResult",
    "compile_paper",
    "format_markdown",
    "get_input_sha256",
    "validate_markdown",
    "verify_compilation",
]
