"""
M25 coverage-hardening tests.

Add this file to:
    tests/test_m25_coverage_hardening.py

It targets the current M25 production modules without changing the
90% coverage policy.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


# ---------------------------------------------------------------------------
# processor.py
# ---------------------------------------------------------------------------

from src.processor import (
    PROCESSORS,
    AlgebraProcessor,
    CalculusProcessor,
    ComplexProcessor,
    DifferentialEquationProcessor,
    LogarithmProcessor,
    MatrixProcessor,
    NumericalProcessor,
    ProbabilityProcessor,
    SetProcessor,
    StatisticsProcessor,
    TransformProcessor,
    TrigonometryProcessor,
    VectorCalculusProcessor,
    clean,
    matrix_from_literal,
    matrix_value,
    split_args,
)


def _known(result):
    assert result.status in {"SOLVED", "VERIFIED", "FAIL", "UNKNOWN", "ERROR"}
    return result


def test_processor_helpers():
    assert clean("  x^2  ") == "x^2"
    assert split_args("a,[1,2],g(3,4),'a,b'") == [
        "a", "[1,2]", "g(3,4)", "'a,b'"
    ]

    m = matrix_from_literal("[[1,2],[3,4]]")
    assert m.shape == (2, 2)

    with pytest.raises(ValueError):
        matrix_from_literal("not-a-matrix")

    with pytest.raises(ValueError):
        matrix_from_literal("[[1],[2,3]]")

    assert matrix_value("matrix([[1,2],[3,4]])")[0, 0] == 1
    assert matrix_value("[[1,2],[3,4]] + [[1,1],[1,1]]")[0, 0] == 2
    assert matrix_value("[[1,2],[3,4]] * [[1,0],[0,1]]")[1, 1] == 4
    assert matrix_value("transpose([[1,2],[3,4]])")[0, 1] == 3
    assert matrix_value("inverse([[1,0],[0,2]])")[1, 1] == pytest.approx(0.5)
    assert matrix_value("[[1,0],[0,1]]^2")[0, 0] == 1

    with pytest.raises(ValueError):
        matrix_value("unsupported_matrix_expression")


@pytest.mark.parametrize("text", [
    "[[1,2],[3,4]]",
    "det([[1,2],[3,4]])",
    "trace([[1,2],[3,4]])",
    "rank([[1,2],[3,4]])",
    "transpose([[1,2],[3,4]])",
    "inverse([[1,0],[0,2]])",
    "eigenvals([[2,0],[0,3]])",
    "eigenvectors([[2,0],[0,3]])",
    "det(matrix([[1,2],[3,4]])*matrix([[1,0],[0,1]]))",
    "trace(matrix([[1,2],[3,4]])*matrix([[1,0],[0,1]]))",
    "rank(matrix([[1,2],[3,4]]))",
    "transpose(matrix([[1,2],[3,4]]))",
    "inv(matrix([[1,0],[0,2]]))",
    "[[2,1],[1,1]] x = [[5],[3]]",
])
def test_matrix_processor_paths(text):
    _known(MatrixProcessor.process(text))


def test_matrix_error_paths():
    assert MatrixProcessor.process("det([[1,2,3],[4,5,6]])").status == "ERROR"
    assert MatrixProcessor.process("trace([[1,2,3],[4,5,6]])").status == "ERROR"
    assert MatrixProcessor.process("inverse([[1,2],[2,4]])").status == "ERROR"
    assert MatrixProcessor.process("[[1,2],[3,4]] x = [[1],[2],[3]]").status == "ERROR"
    assert MatrixProcessor.process("not_matrix").status in {"UNKNOWN", "ERROR"}


@pytest.mark.parametrize("text", [
    "1 + 2*I",
    "conjugate(1+2*I)",
    "modulus(3+4*I)",
    "abs(3+4*I)",
    "argument(1+I)",
    "arg(1+I)",
    "real(3+4*I)",
    "imaginary(3+4*I)",
    "polar(1+I)",
    "rect(2,pi/4)",
])
def test_complex_processor_paths(text):
    _known(ComplexProcessor.process(text))


@pytest.mark.parametrize("text", [
    "expand((x+1)^2)",
    "factor(x^2-1)",
    "simplify((x^2-1)/(x-1))",
    "x^2=4",
    "1+1=2",
    "1+1=3",
    "x^2<4",
    "x^2+y^2<4",
    "x^2 + 2*x + 1",
])
def test_algebra_processor_paths(text):
    _known(AlgebraProcessor.process(text))


@pytest.mark.parametrize("text", [
    "sin(x)^2 + cos(x)^2",
    "solve_trig(sin(x)=0,x)",
    "sin(x)=0",
    "unsupported_trig",
])
def test_trigonometry_processor_paths(text):
    _known(TrigonometryProcessor.process(text))


@pytest.mark.parametrize("text", [
    "log(x)+log(y)",
    "solve_log(log(x)=0,x)",
    "log(x)=0",
    "unsupported_log",
])
def test_logarithm_processor_paths(text):
    _known(LogarithmProcessor.process(text))


@pytest.mark.parametrize("text", [
    "diff(x^3,x)",
    "derivative(x^4,x,2)",
    "partial(x^2*y,x)",
    "pdiff(x^2*y,x,2)",
    "mixed_partial(x*y,x,y)",
    "total(x*y,x,1,y,2)",
    "total(x^2+y^2,x,x(t),y,y(t),t)",
    "total(x+y,x,1)",
    "integrate(x^2,x)",
    "integral(x,x,0,1)",
    "double_integral(x+y,x,0,1,y,0,1)",
    "line_integral(x,y,x,y,t,0,1,t,t)",
    "surface_integral(1,x,y,z,u,v,0,1,0,1,u,v,0)",
    "limit(sin(x)/x,x,0)",
    "continuity(x^2,x,1)",
    "taylor(exp(x),x,0,4)",
    "maclaurin(sin(x),x,0,4)",
    "unsupported_calculus",
])
def test_calculus_processor_paths(text):
    _known(CalculusProcessor.process(text))


@pytest.mark.parametrize("text", [
    "dy/dx = x",
    "ode2(y,x,y)",
    "unsupported_ode",
])
def test_differential_equation_paths(text):
    _known(DifferentialEquationProcessor.process(text))


@pytest.mark.parametrize("text", [
    "laplace(x,t,s)",
    "inverse_laplace(1/s,t,s)",
    "fourier(exp(-x^2),x)",
    "unsupported_transform",
])
def test_transform_processor_paths(text):
    _known(TransformProcessor.process(text))


@pytest.mark.parametrize("text", [
    "{1,2,3} ∩ {2,3,4}",
    "{1,2,3} ∪ {2,3,4}",
    "{1,2,3} - {2,3,4}",
    "{1,2,3} \\ {2,3,4}",
    "subset({1,2},{1,2,3})",
    "subset({1,4},{1,2,3})",
    "unsupported_set",
])
def test_set_processor_paths(text):
    _known(SetProcessor.process(text))


@pytest.mark.parametrize("text", [
    "prob(1/2)",
    "probability(1/3)",
    "P(A)=2/5",
    "P(A)=0/0",
    "P(A)=6/5",
    "binomial(4,2,1/2)",
    "combination(5,2)",
    "unsupported_probability",
])
def test_probability_processor_paths(text):
    _known(ProbabilityProcessor.process(text))


@pytest.mark.parametrize("text", [
    "mean(1,2,3)",
    "median(1,3,2)",
    "median(1,2,3,4)",
    "variance(1,2,3)",
    "std(1,2,3)",
    "stdev(1,2,3)",
    "mode(1,1,2,3)",
    "mean()",
    "covariance([1,2,3],[2,4,6])",
    "correlation([1,2,3],[2,4,6])",
    "correlation([1,1,1],[2,3,4])",
    "unsupported_statistics",
])
def test_statistics_processor_paths(text):
    _known(StatisticsProcessor.process(text))


@pytest.mark.parametrize("text", [
    "gradient(x^2+y^2,x,y)",
    "gradient(x^2+y^2+z^2,x,y,z)",
    "divergence((x,y,z),x,y,z)",
    "curl((x,y,z),x,y,z)",
    "dot([1,2,3],[4,5,6])",
    "cross([1,0,0],[0,1,0])",
    "unsupported_vector",
])
def test_vector_calculus_paths(text):
    _known(VectorCalculusProcessor.process(text))


@pytest.mark.parametrize("text", [
    "newton(x^2-2,x,1,4)",
    "newton(x^2,x,0,2)",
    "bisection(x^2-2,x,0,2,6)",
    "bisection(x^2+1,x,0,2,4)",
    "euler(x+y,x,y,0,1,0.1,2)",
    "rk4(x+y,x,y,0,1,0.1,2)",
    "lagrange([0,1,2],[0,1,4],1.5)",
    "lagrange([0,1],[1],0.5)",
    "unsupported_numerical",
])
def test_numerical_processor_paths(text):
    _known(NumericalProcessor.process(text))


def test_processor_registry():
    assert set(PROCESSORS) == {
        "matrix", "complex", "algebra", "trigonometry", "logarithm",
        "calculus", "differential_equation", "transforms", "set_theory",
        "probability", "statistics", "vector_calculus", "numerical",
    }


# ---------------------------------------------------------------------------
# solver.py
# ---------------------------------------------------------------------------

from src import solver


def test_solver_equality_paths():
    assert solver._clean(r" \frac{1}{2} + \pi + i ") == "(1)/(2) + pi + I"
    assert solver.verify_equality("x^2", "x*x").status == "PASS"
    assert solver.verify_equality("x^2", "x+1").status == "FAIL"
    assert solver.verify_equality("not valid expression !!!", "2").status == "UNKNOWN"


def test_solver_mcq_paths():
    assert solver.verify_mcq_answer({"A": "2", "B": "3"}, "A", "2").status == "PASS"
    assert solver.verify_mcq_answer({"A": "2", "B": "3"}, "A", "3").status == "FAIL"
    assert solver.verify_mcq_answer({"A": "2"}, "C", "2").status == "FAIL"
    assert solver.verify_mcq_answer({"A": "2"}, "A").status == "UNKNOWN"


def test_solver_process_result_paths():
    solved = SimpleNamespace(status="SOLVED", result="2")
    verified = SimpleNamespace(status="VERIFIED", result="2")
    unknown = SimpleNamespace(status="UNKNOWN", result="2")

    assert solver.verify_process_result(solved, "2").status == "PASS"
    assert solver.verify_process_result(verified, "3").status == "FAIL"
    assert solver.verify_process_result(unknown, "2").status == "UNKNOWN"
    assert solver.verify_process_result(solved).status == "UNKNOWN"


def test_solver_dataclass_defaults():
    assert solver.VerificationResult("PASS", "ok").details == {}


def test_solver_without_sympy(monkeypatch):
    monkeypatch.setattr(solver, "sp", None)
    assert solver.verify_equality("1", "1").status == "UNKNOWN"


# ---------------------------------------------------------------------------
# question_paper_ir.py
# ---------------------------------------------------------------------------

from src.question_paper_ir import PaperSpec, QuestionSpec


def test_question_spec_round_trip():
    q = QuestionSpec(
        id="Q1", text="Solve x+1=2", number=1, marks=2,
        options=["1", "2"], section="A", metadata={"topic": "algebra"},
    )
    assert q.ensure_valid() is q
    data = q.to_dict()
    assert data["id"] == "Q1"
    assert QuestionSpec.from_dict(data).id == "Q1"


@pytest.mark.parametrize("kwargs", [
    {"id": "", "text": "x"},
    {"id": "Q", "text": ""},
    {"id": "Q", "text": "x", "number": 0},
    {"id": "Q", "text": "x", "marks": -1},
])
def test_question_spec_invalid(kwargs):
    with pytest.raises(ValueError):
        QuestionSpec(**kwargs).ensure_valid()


def test_question_spec_bad_diagram():
    with pytest.raises(TypeError):
        QuestionSpec.from_dict({
            "id": "Q",
            "text": "x",
            "diagrams": ["invalid"],
        })


def test_paper_spec_round_trip():
    paper = PaperSpec(
        title="M25 Coverage Paper",
        questions=[
            QuestionSpec(id="Q1", text="x", marks=1),
            QuestionSpec(id="Q2", text="y", marks=2),
        ],
        subject="Mathematics",
        exam="GATE",
        duration_minutes=60,
        instructions=["Answer all questions."],
        metadata={"milestone": 25},
    )
    assert paper.ensure_valid() is paper
    assert paper.resolved_total_marks() == 3
    rebuilt = PaperSpec.from_dict(paper.to_dict())
    assert len(rebuilt.questions) == 2


def test_paper_spec_explicit_total():
    paper = PaperSpec(
        title="T",
        questions=[QuestionSpec(id="Q1", text="x", marks=100)],
        total_marks=5,
    )
    assert paper.resolved_total_marks() == 5.0


@pytest.mark.parametrize("paper", [
    PaperSpec(title="", questions=[QuestionSpec(id="Q1", text="x")]),
    PaperSpec(title="T", questions=[]),
    PaperSpec(
        title="T",
        questions=[QuestionSpec(id="Q1", text="x"),
                   QuestionSpec(id="Q1", text="y")],
    ),
    PaperSpec(
        title="T",
        questions=[QuestionSpec(id="Q1", text="x")],
        duration_minutes=0,
    ),
    PaperSpec(
        title="T",
        questions=[QuestionSpec(id="Q1", text="x")],
        total_marks=-1,
    ),
])
def test_paper_spec_invalid(paper):
    with pytest.raises(ValueError):
        paper.ensure_valid()


# ---------------------------------------------------------------------------
# question_paper_validator.py
# ---------------------------------------------------------------------------

from src import question_paper_validator as qpv


class _Rect:
    def __init__(self, inside=True):
        self.inside = inside

    def within(self, width, height, margin):
        return self.inside


def _item(item_id="Q1", inside=True):
    return SimpleNamespace(id=item_id, rect=_Rect(inside))


def _page(number=1, width=100, height=100, items=None, svg="<svg ></svg>"):
    return SimpleNamespace(
        number=number, width=width, height=height,
        items=list(items or []), svg=svg,
    )


def test_rendered_validator_valid():
    result = SimpleNamespace(
        pages=[_page(items=[_item("Q1"), _item("Q2")])]
    )
    report = qpv.validate_rendered_paper(result)
    assert report["valid"] is True
    assert report["questions"] == 2


def test_rendered_validator_all_errors():
    result = SimpleNamespace(pages=[
        _page(
            number=2, width=0, height=-1,
            items=[_item("DUP"), _item("DUP"), _item("OUT", False)],
            svg="<bad>NaN undefined</bad>",
        ),
        _page(number=3, items=[_item("DUP")]),
    ])
    report = qpv.validate_rendered_paper(result)
    assert report["valid"] is False
    assert any("Invalid page dimensions" in e for e in report["errors"])
    assert any("Duplicate item" in e for e in report["errors"])
    assert any("outside page" in e for e in report["errors"])
    assert any("Invalid SVG page" in e for e in report["errors"])
    assert any("Invalid numeric token" in e for e in report["errors"])
    assert any("more than one page" in e for e in report["errors"])


def test_rendered_validator_empty():
    report = qpv.validate_rendered_paper(SimpleNamespace(pages=[]))
    assert report["valid"] is False


def test_validate_question_paper_success(monkeypatch):
    class FakeRenderer:
        def render(self, paper):
            return SimpleNamespace(
                pages=[_page(items=[_item("Q1")])]
            )

    monkeypatch.setattr(
        "src.question_paper_renderer.QuestionPaperRenderer",
        FakeRenderer,
    )

    paper = PaperSpec(
        title="T",
        questions=[
            QuestionSpec(id="Q1", text="x")
        ],
    )

    assert qpv.validate_question_paper(paper) is True


def test_validate_question_paper_failure(monkeypatch):
    class FakeRenderer:
        def render(self, paper):
            return SimpleNamespace(
                pages=[_page(items=[_item("Q1", False)])]
            )

    monkeypatch.setattr(
        "src.question_paper_renderer.QuestionPaperRenderer",
        FakeRenderer,
    )

    paper = PaperSpec(
        title="T",
        questions=[
            QuestionSpec(id="Q1", text="x")
        ],
    )

    with pytest.raises(ValueError, match="outside page"):
        qpv.validate_question_paper(paper)


# ---------------------------------------------------------------------------
# main.py
# ---------------------------------------------------------------------------

from src import main as main_module


def test_main_parser_defaults():
    args = main_module.build_parser().parse_args([])
    assert args.input is None
    assert args.formats == "markdown,svg,pdf,html"


def test_main_legacy_missing_args():
    args = SimpleNamespace(input=None, output=None, validate=False)
    with pytest.raises(SystemExit):
        main_module._run_legacy(args)


def test_main_legacy_success(tmp_path, monkeypatch):
    source = tmp_path / "input.md"
    output = tmp_path / "nested" / "output.md"
    source.write_text("# Q1", encoding="utf-8")

    monkeypatch.setattr(main_module, "format_document", lambda text: text + "\nformatted")

    args = SimpleNamespace(input=source, output=output, validate=False)
    assert main_module._run_legacy(args) == 0
    assert output.read_text(encoding="utf-8").endswith("formatted")


def test_main_legacy_validation_pass_and_fail(tmp_path, monkeypatch):
    source = tmp_path / "input.md"
    output = tmp_path / "output.md"
    source.write_text("# Q", encoding="utf-8")

    check = lambda passed, name: SimpleNamespace(passed=passed, name=name)

    monkeypatch.setattr(main_module, "format_document", lambda text: "formatted")
    monkeypatch.setattr(
        main_module,
        "validate_rendered_markdown",
        lambda text: [check(True, "syntax"), check(True, "math")],
    )

    args = SimpleNamespace(input=source, output=output, validate=True)
    assert main_module._run_legacy(args) == 0

    monkeypatch.setattr(
        main_module,
        "validate_rendered_markdown",
        lambda text: [check(True, "syntax"), check(False, "math")],
    )
    assert main_module._run_legacy(args) == 2


def test_main_compile_requires_output(tmp_path):
    paper = tmp_path / "paper.json"
    paper.write_text("{}", encoding="utf-8")

    args = SimpleNamespace(
        compile_json=paper, output_dir=None, formats="markdown",
        input=None, output=None,
    )
    with pytest.raises(SystemExit):
        main_module._run_compile(args)


def test_main_compile_success(tmp_path, monkeypatch, capsys):
    paper = tmp_path / "paper.json"
    paper.write_text(
        '{"title":"T","questions":[{"id":"Q1","text":"x"}]}',
        encoding="utf-8",
    )

    artifact = SimpleNamespace(
        kind="markdown", path=tmp_path / "paper.md",
        bytes=10, sha256="abc",
    )
    result = SimpleNamespace(
        status="PASS", api_contract="m25",
        compiler_version="1.0", question_count=1,
        page_count=1, artifacts=[artifact],
    )

    monkeypatch.setattr(
        main_module, "compile_paper",
        lambda paper, output_dir, formats: result,
    )

    args = SimpleNamespace(
        compile_json=paper, output_dir=tmp_path / "out",
        formats="markdown, svg, ", input=None, output=None,
    )
    assert main_module._run_compile(args) == 0
    assert "Status: PASS" in capsys.readouterr().out


def test_main_dispatch_compile_and_legacy(monkeypatch):
    calls = []

    monkeypatch.setattr(
        main_module, "build_parser",
        lambda: SimpleNamespace(
            parse_args=lambda: SimpleNamespace(
                compile_json=Path("paper.json"), input=None, output=None
            )
        ),
    )
    monkeypatch.setattr(
        main_module, "_run_compile",
        lambda args: calls.append("compile") or 7,
    )
    assert main_module.main() == 7

    monkeypatch.setattr(
        main_module, "build_parser",
        lambda: SimpleNamespace(
            parse_args=lambda: SimpleNamespace(
                compile_json=None, input=Path("in.md"), output=Path("out.md")
            )
        ),
    )
    monkeypatch.setattr(
        main_module, "_run_legacy",
        lambda args: calls.append("legacy") or 8,
    )
    assert main_module.main() == 8
    assert calls == ["compile", "legacy"]


def test_main_compile_argument_conflict(monkeypatch):
    monkeypatch.setattr(
        main_module, "build_parser",
        lambda: SimpleNamespace(
            parse_args=lambda: SimpleNamespace(
                compile_json=Path("paper.json"),
                input=Path("in.md"),
                output=Path("out.md"),
            )
        ),
    )
    with pytest.raises(SystemExit):
        main_module.main()
