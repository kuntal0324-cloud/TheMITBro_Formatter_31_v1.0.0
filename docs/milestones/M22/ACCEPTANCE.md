# Milestone 22 — Large-Scale Regression Testing

## Scope

M22 establishes a repeatable regression harness across the complete M15–M21 pipeline.

### Regression coverage

- 76 representative diagram-generation cases
- all 19 M17/M18 diagram families
- detection regression
- mathematical/engineering processor separation
- SVG XML validity
- NaN/undefined output checks
- deterministic generation checks
- M19 layout determinism and validation
- M20 question-paper composition
- M21 PDF production
- M21 self-contained HTML production
- preservation of M17/M18/M21 representative artifacts

## Boundary

M22 is a **testing milestone**, not a new mathematical processor or renderer.

It does not claim that 76 cases exhaustively represent every mathematical expression or every engineering topology. It establishes the infrastructure and representative corpus needed for larger regression expansion.

## Acceptance gate

The complete pytest suite must pass, the M22 corpus must remain balanced across all 19 diagram families, and all representative generated/production artifacts must validate.

GitHub Actions is the external acceptance gate.
