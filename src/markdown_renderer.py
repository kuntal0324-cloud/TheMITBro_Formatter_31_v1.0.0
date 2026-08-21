from __future__ import annotations
import re
from typing import List
from .math_normalizer import normalize_expression, validate_expression

def normalize_latex(value:str)->str:
    return normalize_expression(value)

def normalize_math_text(value:str)->str:
    return normalize_expression(value)

def _matrix_rows(lines:List[str]):
    rows=[]
    for line in lines:
        s=line.strip()
        if not (s.startswith("[") and s.endswith("]")): return None
        s=s[1:-1].strip()
        parts=[p.strip() for p in re.split(r"\s*,\s*|\s{2,}|\s+\|\s+|\s+",s) if p.strip()]
        if not parts:return None
        rows.append(parts)
    if not rows or len({len(r) for r in rows})!=1:return None
    return rows

def matrix_to_latex(rows):
    body=r" \\ ".join(" & ".join(normalize_math_text(x) for x in row) for row in rows)
    return rf"\begin{{bmatrix}}{body}\end{{bmatrix}}"

def _looks_like_matrix_line(line):
    s=line.strip()
    return s.startswith("[") and s.endswith("]") and len(s)>=3

def _convert_matrix_blocks(lines):
    out=[]; i=0
    while i<len(lines):
        if _looks_like_matrix_line(lines[i]):
            j=i; block=[]
            while j<len(lines) and _looks_like_matrix_line(lines[j]):
                block.append(lines[j]); j+=1
            rows=_matrix_rows(block)
            if rows:
                out += ["$$",matrix_to_latex(rows),"$$"]; i=j; continue
        out.append(lines[i]); i+=1
    return out

def _convert_labeled_matrix(lines):
    out=[]; i=0
    label_re=re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*$")
    while i<len(lines):
        m=label_re.match(lines[i])
        if m and i+1<len(lines) and _looks_like_matrix_line(lines[i+1]):
            j=i+1; block=[]
            while j<len(lines) and _looks_like_matrix_line(lines[j]):
                block.append(lines[j]); j+=1
            rows=_matrix_rows(block)
            if rows:
                out += ["$$",f"{m.group(1)} = {matrix_to_latex(rows)}","$$"]; i=j; continue
        out.append(lines[i]); i+=1
    return out

def _looks_math(s):
    if not s or len(s)>220:return False
    # A line containing ordinary prose is not mathematical just because it has i, x, etc.
    if re.search(r"\b(?:find|solve|evaluate|calculate|let|where|since|therefore|the|which|for|if|then|is|are|given|matrix|question|answer)\b",s,re.I):
        return False
    if re.search(r"(?:=|<=|>=|<|>|\^|[+\-*/]|\\(?:frac|sqrt|int|sum|prod|lim|partial|nabla)|∫|∑|√|≤|≥|≠|∞|∈|∉|∩|∪|⊂|⊆|⊃|⊇|∂|∇|π|θ|λ|μ|σ|φ|ω|Δ|δ|α|β|γ|²|³|⁴|⁵|⁶|⁷|⁸|⁹|⁰|¹|±|∓|×|÷|−|→|⇒|⇔)",s):
        return bool(re.fullmatch(r"[\w\s\\{}()[\],.=+\-*/^<>|∫∑∏√∞≤≥≠∈∉∩∪⊂⊆⊃⊇∂∇πθλμσφωΔδαβγ²³⁴⁵⁶⁷⁸⁹⁰₀₁₂₃₄₅₆₇₈₉:;]+",s))
    if re.fullmatch(r"(?:det|tr|rank|abs|arg)\s*\([^)]*\)",s,re.I): return True
    return False

def _convert_math_line(line):
    s=line.strip()
    if not s:return line
    if s.startswith("$$") or s.startswith(r"\[") or s.startswith("```") or s.startswith(">"):return line
    # Inline math already present: normalize only math spans, preserving prose.
    if "$" in s:
        def repl(m): return "$"+normalize_latex(m.group(1))+"$"
        s=re.sub(r"\$(?!\$)(.*?)\$(?!\$)",repl,s)
        return s
    # Normalize mathematical Unicode and legacy operator commands embedded in prose.
    # This intentionally does not wrap the prose in math delimiters.
    if re.search(r"(?:\\operatorname\{|\\dfrac|[≤≥≠≈∞∈∉∩∪⊂⊆⊃⊇∂∇√πθλμσφωΔδαβγ²³⁴⁵⁶⁷⁸⁹⁰¹±∓×÷−→⇒⇔])", s):
        return normalize_math_text(s)
    if _looks_math(s):
        return f"${normalize_math_text(s)}$"
    # Common question cues: format the mathematical tail without wrapping prose.
    cue=re.match(r"^(\s*(?:Let|If|Given|Find|Evaluate|Compute|Calculate|Solve|Determine|Show that|Prove that|Hence|Therefore)\s+)(.+)$",s,re.I)
    if cue:
        prefix,tail=cue.groups()
        if re.search(r"(?:=|\^|\bdet\s*\(|\btr\s*\(|\b(?:sin|cos|tan|log|ln)\s*\(|[∫∑∏√≤≥≠∞∂∇])",tail):
            return prefix+"$"+normalize_math_text(tail)+"$"
    # A prose line containing an explicit equality is split at the first math relation.
    if "=" in s and re.search(r"[A-Za-z0-9)]\s*=\s*[A-Za-z0-9(\\]",s):
        m=re.search(r"([A-Za-z][A-Za-z0-9_]*\s*=\s*.+)$",s)
        if m and len(m.group(1))<180:
            return s[:m.start(1)]+"$"+normalize_math_text(m.group(1))+"$"
    return line

def render_question(text:str)->str:
    lines=text.replace("\r\n","\n").replace("\r","\n").split("\n")
    lines=_convert_labeled_matrix(lines); lines=_convert_matrix_blocks(lines)
    rendered=[]; in_display=False
    for line in lines:
        st=line.strip()
        if st=="$$":
            rendered.append(line); in_display=not in_display; continue
        rendered.append(normalize_math_text(line) if in_display else _convert_math_line(line))
    result=[]; blank=0
    for line in rendered:
        if not line.strip():
            blank+=1
            if blank<=2: result.append("")
        else:
            blank=0; result.append(line.rstrip())
    return "\n".join(result).strip()+"\n"
    
