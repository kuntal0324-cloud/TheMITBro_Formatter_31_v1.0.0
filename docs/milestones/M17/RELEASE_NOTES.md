# TheMITbro Formatter — Milestone 17 Release Notes

## Release

**Milestone 17 — Mathematical Diagram Generation**

## What changed

M17 builds the first actual diagram generation layer on top of the M16 Diagram IR.

### New processors

- `src/mathematical_diagram_generator.py`
- `src/diagram_renderer.py`

### Mathematical diagram families

- coordinate geometry
- graphs
- geometric figures
- probability diagrams
- Venn diagrams
- function plots
- number lines
- statistical plots

### Output

The renderer produces deterministic, standalone SVG. SVG was selected as the M17 output boundary because it is portable and can later be embedded into the HTML/PDF layout pipeline without coupling M17 to a final page renderer.

### Validation

- Frozen M15/M16 regression suite preserved
- M17 generation suite: 23 tests
- Complete suite: **106 passed**
- Representative SVG samples: 8
- SVG XML validation: 8/8 passed
- Engineering diagram generation intentionally rejected by M17 and reserved for M18

## Important boundary

M17 is not a universal natural-language diagram solver. It supports explicit canonical requests and structured M16 DiagramSpec input. Ambiguous/unsupported requests fail rather than fabricate a diagram.

## Next

M18 — Engineering Diagram Generation.
