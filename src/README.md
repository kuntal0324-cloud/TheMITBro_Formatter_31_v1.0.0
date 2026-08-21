# Source modules

M18 adds:

- `engineering_diagram_generator.py` — engineering request → DiagramSpec → SVG processor
- `engineering_diagram_renderer.py` — deterministic SVG renderer for the 11 engineering families

M17 remains the mathematical diagram generation boundary.
M19 will own page/layout composition.

M20 adds:

- `question_paper_ir.py` — structured paper/question contract
- `question_paper_renderer.py` — deterministic question-paper SVG composition
- `question_paper_validator.py` — machine-readable page validation

M21 will consume the M20 placement/markup contract for PDF and HTML production.
