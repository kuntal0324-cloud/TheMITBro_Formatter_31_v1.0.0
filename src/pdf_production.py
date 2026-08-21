from __future__ import annotations

from pathlib import Path
from typing import Union
import tempfile

from reportlab.lib.colors import black, white
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

from .question_paper_ir import PaperSpec
from .question_paper_renderer import QuestionPaperRenderer, RenderedPaper


def render_paper_pdf(
    paper: Union[PaperSpec, dict],
    output_path: Union[str, Path],
) -> Path:
    """Render an M20 PaperSpec to a deterministic PDF using reportlab.

    The M20 SVG pages remain the source of truth for composition. svglib
    converts each page SVG to a ReportLab drawing; reportlab writes the PDF.
    """
    if not isinstance(paper, PaperSpec):
        paper = PaperSpec.from_dict(paper)
    result: RenderedPaper = QuestionPaperRenderer().render(paper)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(
        str(path),
        pagesize=(QuestionPaperRenderer().options.width,
                  QuestionPaperRenderer().options.height),
        pageCompression=1,
        invariant=1,
    )
    c.setTitle(paper.title)
    author = paper.metadata.get("author")
    if author:
        c.setAuthor(str(author))

    for page in result.pages:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".svg", encoding="utf-8", delete=False
        ) as temp:
            temp.write(page.svg)
            temp_path = Path(temp.name)
        try:
            drawing = svg2rlg(str(temp_path))
            if drawing is None:
                raise ValueError(
                    f"Unable to convert page {page.number} SVG to PDF."
                )
            renderPDF.draw(drawing, c, 0, 0)
        finally:
            temp_path.unlink(missing_ok=True)
        c.showPage()
    c.save()
    return path


def _svg_with_explicit_dimensions(svg: str) -> str:
    return svg
