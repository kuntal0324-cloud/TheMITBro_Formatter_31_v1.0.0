# TheMITbro Formatter — Milestone 18 Release Notes

## Release

**Milestone 18 — Engineering Diagram Generation**

## What changed

M18 adds the first actual engineering-diagram generation layer on top of the frozen M16 Diagram IR while preserving the M17 mathematical generation boundary.

### New modules

- `src/engineering_diagram_generator.py`
- `src/engineering_diagram_renderer.py`

### Engineering diagram families

- circuit diagrams
- block diagrams
- signal-flow diagrams
- phasor diagrams
- vector diagrams
- transformer equivalent circuits
- motor diagrams
- control-system diagrams
- logic circuits
- engineering waveforms
- network diagrams

### Renderer

The M18 renderer emits standalone deterministic SVG and does not depend on a GUI or image backend.

### Processing model

```text
engineering request
        ↓
diagram detection
        ↓
engineering DiagramSpec
        ↓
M18 processor
        ↓
SVG
```

Structured `DiagramSpec` input is supported in addition to representative canonical natural-language requests.

### Validation

- M15/M16/M17 regression suite preserved
- M18 tests: 21
- Complete suite: **137 passed**
- Representative engineering SVG samples: 11
- SVG XML validation: **11/11 passed**
- No `NaN`/`undefined` output
- Deterministic generation verified
- Invalid topology rejected
- Mathematical-only requests rejected by M18

## Important boundary

M18 is not a universal natural-language engineering diagram solver. It supports the explicit engineering diagram contract and conservative canonical requests. Ambiguous/unsupported requests fail rather than fabricate topology.

M19 owns page/layout composition.

## Next

M19 — Layout Engine.
