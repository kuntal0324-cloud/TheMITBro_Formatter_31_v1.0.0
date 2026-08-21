# TheMITbro Formatter — Milestone 19 Acceptance

## Milestone

**Milestone 19 — Layout Engine**

## Objective

Provide a deterministic geometry/layout layer between the existing diagram IR/generators
(M16-M18) and the future question-paper renderer (M20).

## Required capabilities

- [x] Canvas and content-area geometry
- [x] Margin and gap handling
- [x] Deterministic graph/node layering
- [x] Cycle-safe deterministic fallback
- [x] Explicit-position normalization
- [x] Mathematical geometry fitting
- [x] Engineering component/gate layout regions
- [x] Vector/phasor layout regions
- [x] Waveform/motor layout regions
- [x] Collision detection
- [x] Deterministic overlap resolution
- [x] Connector placement
- [x] Question-block vertical composition
- [x] Machine-readable layout validation/report
- [x] Input `DiagramSpec` remains unchanged
- [x] Representative M17/M18 layout plans generated
- [x] Full regression suite retained

## Acceptance tests

The repository must pass:

- complete regression suite
- dedicated M19 layout tests
- representative layout-plan validation
- deterministic output checks
- canvas-bound checks
- overlap checks

## Acceptance result

M19 implementation was validated locally with:

`160 passed`

The repository must still be run through GitHub Actions after commit. The GitHub
workflow result is the external CI acceptance gate.

## Boundary

M19 produces layout geometry. It does not yet perform complete question-paper rendering,
PDF production, or final HTML document composition. Those belong to later milestones.
