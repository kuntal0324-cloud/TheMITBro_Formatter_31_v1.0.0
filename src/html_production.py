from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Union

from .question_paper_ir import PaperSpec
from .question_paper_renderer import QuestionPaperRenderer, RenderedPaper


def render_paper_html(
    paper: Union[PaperSpec, dict],
    output_path: Union[str, Path],
    *,
    title: str | None = None,
) -> Path:
    """Create a self-contained HTML document containing the M20 SVG pages."""
    if not isinstance(paper, PaperSpec):
        paper = PaperSpec.from_dict(paper)
    result: RenderedPaper = QuestionPaperRenderer().render(paper)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    pages = "\n".join(
        f'<section class="paper-page" data-page="{p.number}">{p.svg}</section>'
        for p in result.pages
    )
    manifest_json = json.dumps(result.manifest, sort_keys=True, separators=(",", ":"))
    manifest_pretty = html.escape(json.dumps(result.manifest, sort_keys=True, indent=2))

    doc_title = html.escape(title or paper.title)
    css = """
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: #e9e9e9; }
    body { font-family: sans-serif; }
    main { padding: 24px 0; }
    .paper-page {
      width: 794px;
      min-height: 1123px;
      margin: 0 auto 24px;
      background: white;
      box-shadow: 0 1px 8px rgba(0,0,0,.18);
      overflow: hidden;
      break-after: page;
      page-break-after: always;
    }
    .paper-page svg { display: block; width: 100%; height: auto; }
    details { max-width: 794px; margin: 0 auto 24px; background: white; padding: 12px; }
    pre { white-space: pre-wrap; }
    @media print {
      html, body { background: white; }
      main { padding: 0; }
      .paper-page { margin: 0; box-shadow: none; }
      details { display: none; }
    }
    """
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{doc_title}</title>
<style>{css}</style>
</head>
<body>
<main>
{pages}
</main>
<script id="themitbro-manifest" type="application/json">{manifest_json}</script>
<details>
<summary>Machine-readable M21 manifest</summary>
<pre>{manifest_pretty}</pre>
</details>
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")
    return path
