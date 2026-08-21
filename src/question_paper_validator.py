from __future__ import annotations

from typing import Any, Dict

from .question_paper_ir import PaperSpec
from .question_paper_renderer import RenderedPaper


def validate_rendered_paper(result: RenderedPaper) -> Dict[str, Any]:
    errors = []
    if not result.pages:
        errors.append("Paper must contain at least one page.")
    question_ids = []
    for page in result.pages:
        if page.width <= 0 or page.height <= 0:
            errors.append(f"Invalid page dimensions: {page.number}")
        seen = set()
        for item in page.items:
            if item.id in seen:
                errors.append(f"Duplicate item on page {page.number}: {item.id}")
            seen.add(item.id)
            if not item.rect.within(page.width, page.height, 0):
                errors.append(f"Item outside page {page.number}: {item.id}")
            question_ids.append(item.id)
        if not page.svg.startswith("<svg ") or not page.svg.endswith("</svg>"):
            errors.append(f"Invalid SVG page {page.number}")
        if "NaN" in page.svg or "undefined" in page.svg:
            errors.append(f"Invalid numeric token on page {page.number}")
    if len(question_ids) != len(set(question_ids)):
        errors.append("A question appears on more than one page.")
    return {
        "valid": not errors,
        "errors": errors,
        "pages": len(result.pages),
        "questions": len(question_ids),
    }


def validate_question_paper(paper: PaperSpec) -> bool:
    paper.ensure_valid()
    from .question_paper_renderer import QuestionPaperRenderer
    result = QuestionPaperRenderer().render(paper)
    report = validate_rendered_paper(result)
    if not report["valid"]:
        raise ValueError("; ".join(report["errors"]))
    return True
