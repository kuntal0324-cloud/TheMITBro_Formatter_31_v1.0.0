"""Milestone 23 - production hardening and coverage gate tests."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from src.math_normalizer import normalize_expression, validate_expression
from src.render_validator import render_is_valid

ROOT = Path(__file__).resolve().parents[1]


def test_math_normalizer_operator_and_unicode_hardening():
    value = normalize_expression(r"\operatorname{det}(A) ≤ 2, π, √x")
    assert r"\operatorname" not in value
    assert r"\mathrm{det}" in value
    assert r"\leq" in value
    assert r"\pi" in value
    assert r"\sqrt" in value


def test_math_normalizer_limit_and_plain_operator_hardening():
    value = normalize_expression(r"lim x -> 0")
    assert r"\lim_{x\to0}" in value
    assert r"det(A)" not in value
    assert r"\mathrm{det}(A)" in normalize_expression("det(A)")


@pytest.mark.parametrize(
    "expression",
    [
        r"(x+1",
        r"[x+1)",
        r"\left( x \right",
        r"$$x+1",
    ],
)
def test_math_validation_rejects_structural_or_unicode_residue(expression):
    result = validate_expression(expression)
    assert not result.valid
    assert result.warnings


def test_math_validation_detects_unmapped_unicode(monkeypatch):
    import src.math_normalizer as mn
    monkeypatch.setattr(mn, "normalize_expression", lambda value: str(value))
    result = mn.validate_expression("x ≤ y")
    assert not result.valid
    assert any("Unicode" in warning for warning in result.warnings)


def test_math_validation_accepts_normalized_expression():
    result = validate_expression(r"\mathrm{det}(A)=1")
    assert result.valid
    assert result.warnings == []


def test_render_validator_rejects_unbalanced_display_math():
    assert not render_is_valid("$$x+1")


def test_cli_formats_and_validates_input(tmp_path):
    source = tmp_path / "question.md"
    output = tmp_path / "out.md"
    source.write_text(
        r"For A, use $\operatorname{det}(A)=1$.",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.main",
            str(source),
            "-o",
            str(output),
            "--validate",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert output.is_file()
    text = output.read_text(encoding="utf-8")
    assert r"\operatorname" not in text
    assert "Formatted:" in result.stdout



def test_main_module_success_path(tmp_path, monkeypatch):
    import runpy

    source = tmp_path / "module.md"
    output = tmp_path / "module-out.md"
    source.write_text(r"A = 1", encoding="utf-8")
    monkeypatch.setattr(
        sys, "argv", ["src.main", str(source), "-o", str(output)]
    )
    with pytest.raises(SystemExit) as exc: 
        runpy.run_module("src.main", run_name="__main__")
    assert exc.value.code == 0
    assert output.is_file()


def test_main_module_validation_failure_path(tmp_path, monkeypatch):
    import runpy

    source = tmp_path / "module-invalid.md"
    output = tmp_path / "module-invalid-out.md"
    source.write_text("$$x+1", encoding="utf-8")
    monkeypatch.setattr(
        sys, "argv", ["src.main", str(source), "-o", str(output), "--validate"]
    )
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("src.main", run_name="__main__")
    assert exc.value.code == 2


def test_cli_rejects_invalid_render(tmp_path):
    source = tmp_path / "invalid.md"
    output = tmp_path / "invalid-out.md"
    source.write_text("$$x+1", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.main",
            str(source),
            "-o",
            str(output),
            "--validate",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "FAIL:" in result.stdout
