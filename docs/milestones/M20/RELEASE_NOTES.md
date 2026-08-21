# Milestone 20 Release Notes

## Added

- `src/question_paper_ir.py`
  - `QuestionSpec`
  - `PaperSpec`
- `src/question_paper_renderer.py`
  - deterministic paper/page SVG rendering
  - M19 question-block composition
  - question pagination
  - marks/options/header/footer support
  - M17/M18 diagram embedding
- `src/question_paper_validator.py`
  - machine-readable paper validation
- `tests/test_milestone20_question_paper_renderer.py`
  - focused M20 regression tests

## Architectural position

```text
M15 mathematics / normalization
          ↓
M16 Diagram IR
          ↓
M17 mathematical SVG       M18 engineering SVG
          \                    /
           \                  /
              M19 Layout
                   ↓
            M20 Question Paper
                   ↓
             M21 PDF / HTML
```

M20 deliberately stops before final PDF/HTML production.
