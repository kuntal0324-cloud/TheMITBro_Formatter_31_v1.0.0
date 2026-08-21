# TheMITbro Formatter — Milestone 20

M20 is the question-paper composition layer.

## Programmatic example

```python
from src.question_paper_ir import PaperSpec, QuestionSpec
from src.question_paper_renderer import QuestionPaperRenderer

paper = PaperSpec(
    title="GATE EE Practice Paper",
    subject="Electrical Engineering",
    duration_minutes=60,
    questions=[
        QuestionSpec("q1", "Find $2+3$.", number=1, marks=2),
    ],
)

rendered = QuestionPaperRenderer().render(paper)
print(rendered.to_dict())
print(rendered.pages[0].svg)
```

## Boundary

M20 produces deterministic SVG pages and a placement manifest. M21 is responsible
for final PDF/HTML production and publication packaging.
