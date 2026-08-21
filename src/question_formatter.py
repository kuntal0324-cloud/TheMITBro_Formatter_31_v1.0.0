from __future__ import annotations
import re
from .markdown_renderer import render_question

def format_document(text:str)->str:
    text=text.replace("\r\n","\n").replace("\r","\n").strip()
    text=re.sub(r"(?m)^##?\s*([A-Z]+-[A-Z]+-\d+)\s*$",r"### \1",text)
    for field in ("Subject","Topic","Total Questions"):
        text=re.sub(rf"(?ms)^##\s+{re.escape(field)}\s*\n([^#\n]+)",
                    lambda m:f"**{field}:** {m.group(1).strip()}",text)
    return render_question(text)
