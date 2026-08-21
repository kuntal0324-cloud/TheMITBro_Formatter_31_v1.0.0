# TheMITbro Formatter — M30 Release Candidate

> **Current development status: M30 — Release Candidate / Repository Freeze**

M22–M29 established regression, production hardening, release contracts, reproducibility, end-to-end quality, real-world corpus compatibility, and formatter completeness. M30 consolidates the repository documentation and validates the current implementation as a production release candidate.

## Documentation

- [Roadmap](docs/ROADMAP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Format Specification](docs/FORMAT_SPECIFICATION.md)
- [Release Process](docs/RELEASE_PROCESS.md)
- [Milestone History](docs/milestones/README.md)

## Historical milestone notes

The following sections preserve historical implementation notes from earlier milestones. The authoritative milestone records are organized under `docs/milestones/`.

M17 is the mathematical diagram generation stage built on the frozen M16 Diagram IR.

## Full Mathematical Solver + Mathematical Rendering Validation

Milestone 15 is the **mathematical-computation completion stage** before the project moves to diagram representation in Milestone 16.

### What this milestone actually delivers

The engine now has a unified `SolverEngine` that:

1. normalizes the input,
2. detects the mathematical domain,
3. dispatches to a domain processor,
4. computes with SymPy where symbolic computation is appropriate,
5. returns a uniform `ProcessResult`,
6. exposes a canonical LaTeX representation,
7. refuses to invent missing information by returning `UNKNOWN` for unsupported forms,
8. provides independent symbolic verification utilities,
9. is covered by an automated regression suite,
10. runs automatically through GitHub Actions.

### Mathematical domains

| Domain | Implemented capabilities |
|---|---|
| Complex numbers | arithmetic, simplification, real/imaginary parts, modulus, argument, conjugate, polar/rectangular forms |
| Algebra | simplification, expansion, factorisation, equations, one-variable inequalities |
| Matrices | construction, addition, multiplication, determinant, trace, rank, transpose, inverse, powers, eigenvalues/eigenvectors, linear systems, nested/mixed matrix expressions |
| Trigonometry | simplification and real-domain equation solving |
| Logarithms | logarithmic simplification and real-domain equation solving |
| Calculus | limits, continuity, first/higher derivatives, partial/mixed derivatives, total derivatives, indefinite/definite integrals, double integrals, line integrals, scalar surface integrals, series/Taylor/Maclaurin |
| Differential equations | first-order `dy/dx = RHS` and an extension point for higher-order ODE forms |
| Transforms | Laplace, inverse Laplace, Fourier transform |
| Set theory | finite union, intersection, difference and subset checks |
| Probability | explicit probability expressions, rational probabilities, combinations, binomial probability |
| Statistics | mean, median, population variance/std, mode, covariance, correlation |
| Vector calculus | gradient, divergence, curl, dot product, cross product |
| Numerical methods | Newton, bisection, Euler, RK4, Lagrange interpolation |
| Rendering/normalization | matrices, operators, fractions, Unicode mathematical symbols, superscripts/subscripts, existing inline/display math |
| Verification | symbolic equality and MCQ-result verification |

### Architectural boundary

Milestone 15 is deliberately **not** the diagram engine.

The agreed project sequence remains:

```text
M1–13  Foundation
   ↓
M14    Unified Solver Engine
   ↓
M15    Full Mathematical Solver  ← current milestone
   ↓
M16    Diagram Representation
   ↓
M17    Mathematical Diagram Generation
   ↓
M18    Engineering Diagram Generation
   ↓
M19    Layout Engine
   ↓
M20    Question-Paper Renderer
   ↓
M21    PDF / HTML Production
   ↓
M22    Large-scale Regression Testing
   ↓
M23    Production Hardening
```

### Important engineering rule

This is **not a universal natural-language solver**. The processor API accepts structured mathematical expressions and representative canonical forms. Unsupported or ambiguous syntax returns `UNKNOWN` rather than fabricating an answer.

That distinction is intentional. A green test run proves that the supported contract is working; it does not prove that every possible GATE/JEE/engineering question can be solved.

## Running locally

```bash
python -m pytest -q
```

The Milestone 15 acceptance suite currently contains **70 automated tests**.

Format and validate a Markdown document:

```bash
python -m src.main input/milestone15_representative.md \
  -o output/milestone15_representative.md \
  --validate
```

## Running on GitHub

The workflow is:

```text
.github/workflows/tests.yml
        ↓
checkout
        ↓
Python 3.11
        ↓
install requirements
        ↓
pytest
        ↓
PASS / FAIL
```

GitHub Actions workflows are stored under `.github/workflows` and can run on pushes, pull requests, or manual dispatch. See the official GitHub Actions documentation for the workflow model and CI behavior. 

## Acceptance condition

Milestone 15 is considered technically complete when:

- the repository imports cleanly,
- the formatter validates representative mathematical Markdown,
- every registered domain has representative tests,
- mixed matrix expressions are tested,
- rendering normalization is tested,
- independent verification is tested,
- the complete pytest suite passes,
- GitHub Actions passes the same suite.

The supplied build has been tested locally with:

```text
70 passed
```

No diagram generation is included here by design; that begins at Milestone 16.

## Milestone 15 — Final Status

**Status: COMPLETE ✅**

Milestone 15.1 hardening has been completed.

Final validation:
- Automated test suite: 70/70 passing
- GitHub Actions: passing
- Mathematical rendering validation: passing
- LaTeX normalization: passing
- Matrix rendering: passing
- Inline mathematical rendering: passing
- Rendering validation: passing
- Regression validation: passing

Milestone 15 is now frozen as the baseline for Milestone 16.

No Milestone 16 implementation is included in this release.


## Milestone 16 — Diagram Representation

M16 adds the unified Diagram Intermediate Representation (IR) for the agreed mathematical and engineering diagram families. It separates structural representation from later rendering. Mathematical generation begins in M17; engineering generation begins in M18.


## Milestone 16 — Diagram Representation

M16 adds the unified Diagram Intermediate Representation (IR) for the agreed mathematical and engineering diagram families. It separates structural representation from later rendering. Mathematical generation begins in M17; engineering generation begins in M18.


## Milestone 16 — Diagram Representation

M16 adds the unified Diagram Intermediate Representation (IR) for the agreed mathematical and engineering diagram families. It separates structural representation from later rendering. Mathematical generation begins in M17; engineering generation begins in M18.

## Milestone 17 — Mathematical Diagram Generation

M17 adds a deterministic SVG generation layer for the eight mathematical diagram families defined by M16.

### Mathematical generation

| Family | M17 generation |
|---|---|
| Coordinate geometry | SVG axes, grid, points, labels |
| Graphs | SymPy-backed expression sampling and polylines |
| Geometric figures | polygons, triangles, circles and labels |
| Probability diagrams | node/edge probability trees |
| Venn diagrams | two-/three-set Venn layout |
| Function plots | SymPy-backed function sampling |
| Number lines | axis, ticks, marked values and labels |
| Statistical plots | scatter, histogram and box plot |

### New modules

```text
src/
├── diagram_renderer.py
└── mathematical_diagram_generator.py
```

`diagram_renderer.py` is the deterministic SVG backend.

`mathematical_diagram_generator.py` is the M17 processor that performs detection → IR construction → validation → SVG generation.

### Programmatic use

```python
from src.mathematical_diagram_generator import generate_mathematical_diagram

result = generate_mathematical_diagram("Plot f(x) = x^2 + 1.")
print(result["diagram_type"])
print(result["svg"])
```

To save SVG:

```python
generate_mathematical_diagram(
    "Draw the coordinate plane with points A (1,2) and B (-2,3).",
    output_path="output/coordinate.svg"
)
```

### M17 boundary

M17 generates mathematical diagrams only. Engineering diagram generation begins in M18.

### Validation

The M17 release retains all M15/M16 regression tests and adds 22 M17 generation tests.

Expected result:

```text
106 passed
```

See `docs/milestones/M17/ACCEPTANCE.md` for the complete acceptance contract.

## Milestone 18 — Engineering Diagram Generation

M18 is the engineering-diagram generation stage built on the frozen M16 Diagram IR and the M17 mathematical SVG boundary.

### Engineering families

| Family | M18 generation |
|---|---|
| Circuit diagrams | wires, R/C/L, voltage/current sources |
| Block diagrams | directed functional blocks |
| Signal-flow diagrams | directed signal paths |
| Phasor diagrams | magnitude/angle vectors |
| Vector diagrams | Cartesian/polar-derived vectors |
| Transformer equivalent circuits | R1, X1, Rc, Xm, R2', X2' structure |
| Motor diagrams | stator/rotor structural view |
| Control-system diagrams | forward and feedback paths |
| Logic circuits | AND, OR, NOT, NAND, NOR, XOR, XNOR |
| Engineering waveforms | sine, square, triangle, sawtooth |
| Network diagrams | deterministic node/edge topology |

### New modules

```text
src/
├── engineering_diagram_generator.py
└── engineering_diagram_renderer.py
```

### Validation

M18 preserves the complete M15/M16/M17 regression baseline and adds 21 engineering generation tests.

Current local validation:

```text
137 passed
```

Representative SVG output:

```text
11 engineering samples
11/11 valid XML
0 NaN
0 undefined
```

### M18 boundary

M18 generates engineering diagrams only. Mathematical diagrams remain owned by M17.

M18 does not yet implement page layout, question-paper composition, PDF pagination, HTML production, large-scale regression, or production hardening.

See:

- `docs/milestones/M18/ACCEPTANCE.md`
- `docs/milestones/M18/RELEASE_NOTES.md`
- `output/milestone18_samples/`

### Project sequence

```text
M15  Mathematical Rendering & Processor Validation   ✅
 ↓
M16  Diagram Representation                           ✅
 ↓
M17  Mathematical Diagram Generation                  ✅
 ↓
M18  Engineering Diagram Generation                   ← current
 ↓
M19  Layout Engine
 ↓
M20  Question-Paper Renderer
 ↓
M21  PDF / HTML Production
 ↓
M22  Large-scale Regression Testing
 ↓
M23  Production Hardening
```

## Current Status

**Milestone 18 is the active development stage.**

Local validation:

```text
137 passed
```

The M18 GitHub Actions workflow is configured to run the complete regression suite, M17 tests, M18 tests, and validation of all 19 representative SVG samples.

M18 should be marked complete only after the GitHub Actions run is green.

## Milestone 19 — Layout Engine

M19 introduces the deterministic layout layer between diagram representation/generation
(M16-M18) and future question-paper composition (M20).

### M19 responsibilities

- canvas, margin, title and content-area geometry
- deterministic node/layer placement for graph-like diagrams
- normalization of explicit positions into a target canvas
- geometry fitting for mathematical points, vectors, regions and engineering components
- collision/overlap detection and deterministic resolution
- connector placement derived from final item centers
- question-block vertical composition for future paper rendering
- machine-readable layout validation and reports
- preservation of M16-M18 semantic `DiagramSpec` data (layout does not mutate the input)

M19 intentionally does **not** replace the M16-M18 renderers. It produces the stable
placement contract that M20 can consume for complete question-paper composition.

Representative layout plans are stored in:

`output/milestone19_layout_samples/`

The M19 acceptance gate is defined in `docs/milestones/M19/ACCEPTANCE.md`.



## Milestone 21
PDF and self-contained HTML production are implemented on top of the stable M20 rendered-paper output. Final large-scale regression and production hardening remain in M22-M23.


## Milestone 25 — Public API & End-to-End Question Compilation

M25 freezes the application-facing formatter contract and adds deterministic
end-to-end question-paper compilation.

### Public API

```python
from src.public_api import (
    API_VERSION,
    compile_paper,
    format_markdown,
    validate_markdown,
)

print(API_VERSION)  # "1.0"
```

The public API is intentionally separated from internal implementation modules.
Application code should use `src.public_api` rather than importing renderer or
layout internals directly.

### End-to-end compiler

A structured `PaperSpec` dictionary can be compiled into production artifacts:

```bash
python -m src.main \
  --compile-json input/milestone25_e2e_paper.json \
  --output-dir output/m25 \
  --formats markdown,svg,pdf,html
```

A successful compilation produces:

```text
output/m25/
├── paper.md
├── paper.svg
├── paper.pdf
├── paper.html
└── manifest.json
```

`manifest.json` records SHA-256 hashes and byte sizes for every generated
production artifact.

### Backward compatibility

The legacy Markdown formatter remains available:

```bash
python -m src.main input/question.md \
  -o output/question.md \
  --validate
```

### M25 CI

```text
.github/workflows/m25-contract.yml
        ↓
source compilation
        ↓
complete regression
        ↓
M24 regression
        ↓
M25 contract tests
        ↓
90% coverage gate
        ↓
public API / CLI audit
        ↓
E2E artifact validation
        ↓
evidence upload
```

See:

- `docs/milestones/M25/ACCEPTANCE.md`
- `docs/milestones/M25/RELEASE_NOTES.md`
- `input/milestone25_e2e_paper.json`
- `tests/test_milestone25_release.py`
- `scripts/m25_contract_audit.py`

## Milestone 26 — Reproducible Build + Artifact Integrity

M26 adds an integrity layer around the frozen M25 compiler contract.

- Canonical SHA-256 identity for structured paper input.
- M26 build contract `26.0` while retaining compiler version `25.0`.
- Self-hashed deterministic `manifest.json`.
- Offline compilation-bundle verification.
- CLI verification via `--verify-output`.
- Dedicated M26 integrity tests and audit.
- Dedicated GitHub Actions integrity workflow.
- M25 regression compatibility remains required.

Verification:

```bash
python -m pytest -q tests/test_milestone26_integrity.py
python -m pytest -q tests/test_milestone25_release.py
python scripts/m26_integrity_audit.py
```

## Milestone 29 — Formatter Completeness + Edge-Case Closure

M29 closes high-value formatter edge cases exposed by the M28 real-world corpus.

- Expanded mathematical Unicode normalization.
- Added superscript `¹` support.
- Added `±`, `∓`, `×`, `÷`, `−`, `→`, `⇒`, and `⇔` normalization.
- Normalizes legacy `\\operatorname` and `\\dfrac` commands embedded in prose.
- Added fail-closed malformed-expression and structured-paper tests.
- Added deterministic line-ending and option-preservation checks.
- Added an independent M29 completeness audit.
- Added `.github/workflows/m29-completeness.yml`.

M29 certification requires the dedicated M29 workflow and the complete regression
pipeline to remain green.
