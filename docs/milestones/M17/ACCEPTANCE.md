# Milestone 17 — Mathematical Diagram Generation Acceptance

## Purpose

M17 converts the mathematical Diagram IR created in M16 into deterministic, portable SVG diagrams.

M17 owns **mathematical diagram generation only**. Engineering diagram generation remains M18.

## Mathematical families implemented

1. Coordinate geometry
2. Graphs
3. Geometric figures
4. Probability diagrams
5. Venn diagrams
6. Function plots
7. Number lines
8. Statistical plots

## Generation pipeline

```text
Question / structured data
        ↓
M16 diagram detection
        ↓
M16 DiagramSpec / Diagram IR
        ↓
M17 mathematical generator
        ↓
deterministic SVG renderer
        ↓
SVG output
```

## Rendering capabilities

- SVG canvas with explicit viewBox
- titles and accessible descriptions
- Cartesian axes and grid
- labeled coordinate points
- mathematical function sampling through SymPy
- discontinuity-safe function polylines
- geometric polygons and circles
- probability-tree nodes and labeled branches
- two-/three-set Venn layouts
- number-line ticks and marked values
- statistical scatter plots
- statistical histograms
- statistical box plots
- deterministic output suitable for later HTML/PDF embedding
- file output through `save_diagram()` / generator `output_path`

## Architectural boundary

M17 does **not** generate:

- circuit diagrams
- block diagrams
- signal-flow diagrams
- phasor diagrams
- engineering vector diagrams
- transformer equivalent circuits
- motor diagrams
- control-system diagrams
- logic circuits
- engineering waveforms
- engineering network diagrams

Those are reserved for M18.

M17 also does not yet implement the final question-paper layout engine, PDF pagination, or production HTML packaging. Those remain later milestones.

## Regression policy

All M15 and M16 tests remain mandatory.

The M17 acceptance suite adds generation and SVG validation tests without weakening earlier tests.

## Acceptance gate

M17 is technically complete when all of the following are true:

- repository structure passes
- complete regression suite passes
- M16 diagram IR tests pass
- all eight mathematical diagram families have generation tests
- generated SVG is structurally valid
- generated output contains no `NaN`/`undefined`
- function plots are sampled from mathematical expressions
- discontinuities do not create misleading cross-asymptote segments
- structured IR generation works
- representative natural-language generation works for supported canonical requests
- engineering diagrams are rejected by the M17 processor
- deterministic generation is verified
- output-file generation is verified
- GitHub Actions passes the same acceptance suite

## Current build baseline

M16 baseline: 83 tests.

M17 adds 23 generation tests.

Expected complete suite for this release:

```text
106 passed
```

## Explicit limitation

A green M17 test suite does **not** mean arbitrary natural-language mathematical diagrams are universally understood. The supported contract is explicit and conservative. Unsupported or ambiguous requests must fail rather than fabricate a diagram.

## Next milestone

```text
M17 Mathematical Diagram Generation  ← current
        ↓
M18 Engineering Diagram Generation
        ↓
M19 Layout Engine
        ↓
M20 Question-Paper Renderer
        ↓
M21 PDF / HTML Production
        ↓
M22 Large-scale Regression Testing
        ↓
M23 Production Hardening
```
