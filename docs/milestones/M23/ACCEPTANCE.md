# Milestone 23 — Production Hardening

## Scope

M23 hardens the M15–M22 production pipeline without introducing a new mathematical or diagram family.

### Hardening gates

- complete M15–M22 regression suite remains green
- CLI success and validation-failure paths are exercised
- LaTeX/operator/Unicode normalization edge cases are tested
- Python source compilation is validated
- overall source line coverage is at least 90%
- critical production modules remain at least 90% covered
- M17/M18 SVG artifacts remain valid XML and free of NaN/undefined tokens
- M19 layout corpus remains valid
- M20/M21 representative production artifacts remain valid
- CI artifact upload uses the Node 24-compatible upload action

## Coverage policy

M23 does **not** require 100% coverage. Coverage is used as an engineering gate, not as a vanity metric. The target is at least 90% overall, with explicit 90% minimums on critical production modules.

## Boundary

M23 does not claim universal mathematical correctness. It strengthens production reliability, regression protection, and CI hygiene around the existing M15–M22 capabilities.

## Acceptance gate

GitHub Actions must report `MILESTONE 23 CI VALIDATION PASSED`.
