# Milestone 15 Acceptance Specification

## Gate A — Infrastructure

- [x] Python package imports
- [x] requirements declared
- [x] pytest suite available
- [x] GitHub Actions workflow available
- [x] push trigger
- [x] pull-request trigger
- [x] manual `workflow_dispatch`

## Gate B — Mathematical normalization/rendering

- [x] `\operatorname{...}` → supported `\mathrm{...}`
- [x] `\dfrac` → `\frac`
- [x] common Unicode operators normalized
- [x] superscripts/subscripts normalized
- [x] matrix rows converted to `bmatrix`
- [x] existing inline math preserved
- [x] display-math delimiter validation
- [x] prose is not blindly converted to math

## Gate C — Domain solving

- [x] complex numbers
- [x] algebra
- [x] matrices / linear algebra
- [x] trigonometry
- [x] logarithms
- [x] calculus
- [x] differential equations
- [x] Laplace/Fourier transforms
- [x] set theory
- [x] probability
- [x] statistics
- [x] vector calculus
- [x] numerical methods

## Gate D — Mixed mathematical expressions

- [x] nested matrix operations
- [x] matrix operations inside determinant/trace
- [x] complex expressions containing arithmetic and powers
- [x] symbolic expressions containing fractions
- [x] calculus expressions involving multiple variables
- [x] vector-calculus expressions
- [x] mathematical output carries LaTeX

## Gate E — Verification

- [x] symbolic equality verification
- [x] failed equality detection
- [x] MCQ answer verification API
- [x] processor result verification API

## Gate F — Regression

- [x] 70 automated tests pass locally
- [ ] GitHub Actions must pass after this exact build is uploaded
- [ ] M15 release should not be declared until the uploaded commit is green

## Explicit non-goals

These are intentionally deferred:

- diagram parsing/representation → M16
- mathematical diagram generation → M17
- engineering diagram generation → M18
- page/layout composition → M19
- question-paper assembly → M20
- PDF/HTML production pipeline → M21
- large-scale corpus regression → M22
- production hardening → M23

## Definition of done

M15 is a **solver/processing milestone**, not a claim of universal AI-level mathematical understanding.

For unsupported syntax, the correct behavior is:

```text
UNKNOWN
```

not a guessed answer.
