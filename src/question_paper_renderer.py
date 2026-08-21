from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
import re
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from .diagram_ir import DiagramSpec, MATHEMATICAL_TYPES
from .diagram_renderer import render_diagram
from .engineering_diagram_renderer import render_engineering_diagram
from .layout_engine import layout_question_blocks
from .layout_ir import LayoutItem, Rect
from .question_formatter import format_document
from .question_paper_ir import PaperSpec, QuestionSpec


@dataclass(frozen=True)
class PaperRenderOptions:
    width: float = 794.0
    height: float = 1123.0
    margin: float = 54.0
    header_height: float = 78.0
    footer_height: float = 28.0
    gap: float = 18.0
    title_font_size: float = 22.0
    body_font_size: float = 14.0
    line_height: float = 20.0
    question_gap: float = 10.0
    diagram_height: float = 230.0
    section_height: float = 26.0

    def validate(self) -> "PaperRenderOptions":
        if self.width <= 2 * self.margin or self.height <= 2 * self.margin:
            raise ValueError("Paper canvas is too small for the requested margin.")
        if min(self.header_height, self.footer_height, self.gap, self.line_height) < 0:
            raise ValueError("Paper layout dimensions must be non-negative.")
        if self.body_font_size <= 0 or self.line_height <= 0:
            raise ValueError("Font size and line height must be positive.")
        return self


@dataclass
class RenderedPage:
    number: int
    width: float
    height: float
    items: List[LayoutItem] = field(default_factory=list)
    svg: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "number": self.number,
            "width": self.width,
            "height": self.height,
            "items": [item.to_dict() for item in self.items],
        }


@dataclass
class RenderedPaper:
    title: str
    pages: List[RenderedPage]
    manifest: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "page_count": len(self.pages),
            "pages": [p.to_dict() for p in self.pages],
            "manifest": self.manifest,
        }

    @property
    def svg(self) -> str:
        return "\n".join(page.svg for page in self.pages)


def _plain_text(value: str) -> str:
    s = str(value)
    s = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
    s = re.sub(r"__(.*?)__", r"\1", s)
    s = re.sub(r"`(.*?)`", r"\1", s)
    return s


def _wrap_text(text: str, max_chars: int) -> List[str]:
    max_chars = max(12, int(max_chars))
    lines: List[str] = []
    for raw in text.splitlines() or [""]:
        raw = _plain_text(raw.strip())
        if not raw:
            lines.append("")
            continue
        words = raw.split()
        current = ""
        for word in words:
            candidate = word if not current else current + " " + word
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    lines.append(current)
                # Long mathematical tokens are hard-wrapped rather than lost.
                while len(word) > max_chars:
                    lines.append(word[:max_chars])
                    word = word[max_chars:]
                current = word
        if current:
            lines.append(current)
    return lines or [""]


def _svg_root_dimensions(svg: str) -> Tuple[float, float]:
    m = re.search(r'<svg\s+[^>]*width="([0-9.]+)"[^>]*height="([0-9.]+)"', svg)
    if not m:
        return 900.0, 600.0
    return float(m.group(1)), float(m.group(2))


def _svg_inner(svg: str) -> str:
    start = svg.find(">")
    end = svg.rfind("</svg>")
    if start < 0 or end < 0 or end <= start:
        raise ValueError("Invalid diagram SVG returned by an earlier milestone.")
    return svg[start + 1:end]


def _diagram_svg(spec: DiagramSpec, width: float, height: float) -> str:
    if spec.diagram_type in MATHEMATICAL_TYPES:
        return render_diagram(spec, width=900, height=600)
    return render_engineering_diagram(spec, width=1000, height=650)


class QuestionPaperRenderer:
    """M20 renderer: question-paper composition on top of the M19 layout contract.

    The output is deterministic SVG plus a machine-readable placement manifest.
    PDF/HTML packaging and final typography are intentionally deferred to M21.
    """

    def __init__(self, options: PaperRenderOptions | None = None):
        self.options = (options or PaperRenderOptions()).validate()

    def render(self, paper: PaperSpec) -> RenderedPaper:
        paper.ensure_valid()
        prepared = [self._prepare_question(q) for q in paper.questions]
        pages_data = self._paginate(paper, prepared)
        pages: List[RenderedPage] = []
        for page_no, question_rows in enumerate(pages_data, start=1):
            pages.append(self._render_page(paper, page_no, question_rows, len(pages_data)))

        manifest = {
            "engine": "M20",
            "deterministic": True,
            "page_count": len(pages),
            "question_count": len(paper.questions),
            "total_marks": paper.resolved_total_marks(),
            "source_layout_engine": "M19",
            "boundary": "question-paper composition; PDF/HTML production belongs to M21",
        }
        return RenderedPaper(paper.title, pages, manifest)

    def _prepare_question(self, q: QuestionSpec) -> Dict[str, Any]:
        normalized = format_document(q.text)
        content_width = self.options.width - 2 * self.options.margin
        max_chars = max(20, int(content_width / (self.options.body_font_size * 0.55)))
        text_lines = _wrap_text(normalized, max_chars)
        option_lines: List[str] = []
        for idx, option in enumerate(q.options):
            label = chr(ord("A") + idx) if idx < 26 else str(idx + 1)
            option_lines.extend(_wrap_text(f"{label}. {_plain_text(option)}", max_chars - 3))
        section_lines = 1 if q.section else 0
        height = (
            (section_lines * self.options.section_height)
            + max(1, len(text_lines)) * self.options.line_height
            + len(option_lines) * self.options.line_height
            + self.options.question_gap
        )
        if q.diagrams:
            height += self.options.diagram_height + self.options.question_gap
        height += 12.0
        return {
            "question": q,
            "text_lines": text_lines,
            "option_lines": option_lines,
            "height": height,
        }

    def _paginate(self, paper: PaperSpec, rows: Sequence[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        content_top = self.options.margin + self.options.header_height
        content_bottom = self.options.height - self.options.margin - self.options.footer_height
        available = content_bottom - content_top
        pages: List[List[Dict[str, Any]]] = []
        current: List[Dict[str, Any]] = []
        used = 0.0
        for row in rows:
            q = row["question"]
            needed = row["height"] + (self.options.gap if current else 0.0)
            if row["height"] > available:
                raise ValueError(f"Question {q.id} is taller than one printable page.")
            if current and used + needed > available:
                pages.append(current)
                current = []
                used = 0.0
                needed = row["height"]
            current.append(row)
            used += needed
        if current:
            pages.append(current)
        return pages

    def _render_page(self, paper: PaperSpec, page_no: int, rows: Sequence[Dict[str, Any]], page_count: int) -> RenderedPage:
        o = self.options
        content_top = o.margin + o.header_height
        content_bottom = o.height - o.margin - o.footer_height
        content_width = o.width - 2 * o.margin

        block_specs: List[Tuple[str, float, float]] = []
        for row in rows:
            block_specs.append((row["question"].id, content_width, row["height"]))

        blocks = layout_question_blocks(
            block_specs,
            width=content_width,
            height=content_bottom - content_top,
            margin=0,
            gap=o.gap,
        )
        shifted: List[LayoutItem] = []
        by_id: Dict[str, LayoutItem] = {}
        for block in blocks:
            shifted_block = LayoutItem(
                block.id,
                "question_block",
                Rect(block.rect.x + o.margin, block.rect.y + content_top, block.rect.width, block.rect.height),
                metadata={"page": page_no},
            )
            shifted.append(shifted_block)
            by_id[block.id] = shifted_block

        svg_parts = [self._svg_open(page_no, page_count), self._header_svg(paper, page_no)]
        for row in rows:
            svg_parts.append(self._question_svg(row, by_id[row["question"].id]))
        svg_parts.append(self._footer_svg(page_no, page_count))
        svg_parts.append("</svg>")
        return RenderedPage(page_no, o.width, o.height, shifted, "".join(svg_parts))

    def _svg_open(self, page_no: int, page_count: int) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.options.width:g}" '
            f'height="{self.options.height:g}" viewBox="0 0 {self.options.width:g} {self.options.height:g}" '
            f'role="document" aria-label="Question paper page {page_no} of {page_count}">'
            f'<rect x="0" y="0" width="100%" height="100%" fill="white"/>'
        )

    def _header_svg(self, paper: PaperSpec, page_no: int) -> str:
        o = self.options
        x = o.margin
        title = escape(paper.title)
        meta = " · ".join(x for x in [paper.exam, paper.subject] if x)
        duration = f"Time: {int(paper.duration_minutes)} min" if paper.duration_minutes else ""
        marks = f"Max Marks: {paper.resolved_total_marks():g}" if paper.total_marks is not None or any(q.marks is not None for q in paper.questions) else ""
        right = " · ".join(x for x in [meta, duration, marks] if x)
        lines = [f'<text x="{x:g}" y="32" font-family="sans-serif" font-size="{o.title_font_size:g}" font-weight="700">{title}</text>']
        if right:
            lines.append(f'<text x="{o.width-o.margin:g}" y="32" text-anchor="end" font-family="sans-serif" font-size="11">{escape(right)}</text>')
        y = 52
        for instruction in paper.instructions[:2]:
            lines.append(f'<text x="{x:g}" y="{y:g}" font-family="sans-serif" font-size="11">{escape(_plain_text(instruction))}</text>')
            y += 15
        lines.append(f'<line x1="{x:g}" y1="{o.margin+o.header_height-10:g}" x2="{o.width-o.margin:g}" y2="{o.margin+o.header_height-10:g}" stroke="#333" stroke-width="1"/>')
        return "".join(lines)

    def _footer_svg(self, page_no: int, page_count: int) -> str:
        y = self.options.height - self.options.margin + 4
        return f'<text x="{self.options.width/2:g}" y="{y:g}" text-anchor="middle" font-family="sans-serif" font-size="10">Page {page_no} of {page_count}</text>'

    def _question_svg(self, row: Dict[str, Any], block: LayoutItem) -> str:
        q: QuestionSpec = row["question"]
        o = self.options
        x = block.rect.x
        y = block.rect.y + 18
        parts: List[str] = []
        number = q.number if q.number is not None else ""
        mark_text = f" [{q.marks:g}]" if q.marks is not None else ""
        section = q.section
        if section:
            parts.append(f'<text x="{x:g}" y="{y:g}" font-family="sans-serif" font-size="12" font-weight="700">{escape(section)}</text>')
            y += o.section_height
        label = f"{number}." if number != "" else f"{q.id}:"
        parts.append(f'<text x="{x:g}" y="{y:g}" font-family="sans-serif" font-size="{o.body_font_size:g}" font-weight="700">{escape(label)}</text>')
        text_x = x + 24
        for line in row["text_lines"]:
            if line:
                parts.append(f'<text x="{text_x:g}" y="{y:g}" font-family="sans-serif" font-size="{o.body_font_size:g}">{escape(line)}</text>')
            y += o.line_height
        if mark_text:
            parts.append(f'<text x="{block.rect.right:g}" y="{block.rect.y+18:g}" text-anchor="end" font-family="sans-serif" font-size="12">{escape(mark_text)}</text>')
        for line in row["option_lines"]:
            if line:
                parts.append(f'<text x="{text_x:g}" y="{y:g}" font-family="sans-serif" font-size="{o.body_font_size:g}">{escape(line)}</text>')
            y += o.line_height
        if q.diagrams:
            y += o.question_gap
            diagram_w = block.rect.width
            diagram_h = min(o.diagram_height, block.rect.bottom - y - 8)
            if diagram_h <= 0:
                raise ValueError(f"Question {q.id} has no room for its diagram.")
            per_h = diagram_h / len(q.diagrams)
            for spec in q.diagrams:
                svg = _diagram_svg(spec, diagram_w, per_h)
                sw, sh = _svg_root_dimensions(svg)
                inner = _svg_inner(svg)
                scale = min(diagram_w / sw, per_h / sh)
                w = sw * scale
                h = sh * scale
                dx = x + (diagram_w - w) / 2
                parts.append(
                    f'<svg x="{dx:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
                    f'viewBox="0 0 {sw:g} {sh:g}" aria-label="{escape(spec.title or spec.diagram_type)}">{inner}</svg>'
                )
                y += per_h
        parts.append(f'<line x1="{x:g}" y1="{block.rect.bottom-2:g}" x2="{block.rect.right:g}" y2="{block.rect.bottom-2:g}" stroke="#ddd" stroke-width="1"/>')
        return "".join(parts)


def render_question_paper(paper: PaperSpec | Dict[str, Any], output_path=None) -> Dict[str, Any]:
    if not isinstance(paper, PaperSpec):
        paper = PaperSpec.from_dict(paper)
    result = QuestionPaperRenderer().render(paper)
    if output_path is not None:
        from pathlib import Path
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # A multi-page SVG is represented as an SVG document containing page groups.
        page_svgs = [p.svg for p in result.pages]
        path.write_text("\n".join(page_svgs), encoding="utf-8")
    return {"paper": result.to_dict(), "pages": [p.svg for p in result.pages], "output_path": str(output_path) if output_path else None}
