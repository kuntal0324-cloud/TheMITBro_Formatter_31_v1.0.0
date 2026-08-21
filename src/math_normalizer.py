from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List

OPERATOR_MAP = {
    r"\operatorname{tr}": r"\mathrm{tr}",
    r"\operatorname{trace}": r"\mathrm{tr}",
    r"\operatorname{det}": r"\mathrm{det}",
    r"\operatorname{rank}": r"\mathrm{rank}",
    r"\operatorname{Re}": r"\mathrm{Re}",
    r"\operatorname{Im}": r"\mathrm{Im}",
    r"\operatorname{arg}": r"\arg",
}
UNICODE_MAP = {
    "≤": r"\leq ", "≥": r"\geq ", "≠": r"\neq ", "≈": r"\approx ",
    "∞": r"\infty ", "∈": r"\in ", "∉": r"\notin ", "∩": r"\cap ", "∪": r"\cup ",
    "⊂": r"\subset ", "⊆": r"\subseteq ", "⊃": r"\supset ", "⊇": r"\supseteq ",
    "∂": r"\partial ", "∇": r"\nabla ", "√": r"\sqrt ", "π": r"\pi ",
    "θ": r"\theta ", "λ": r"\lambda ", "μ": r"\mu ", "σ": r"\sigma ",
    "φ": r"\phi ", "ω": r"\omega ", "Δ": r"\Delta ", "δ": r"\delta ",
    "α": r"\alpha ", "β": r"\beta ", "γ": r"\gamma ", "ε": r"\epsilon ",
    "¹": "^1", "²": "^2", "³": "^3", "⁴": "^4", "⁵": "^5", "⁶": "^6", "⁷": "^7",
    "⁸": "^8", "⁹": "^9", "⁰": "^0",
    "₀": "_0", "₁": "_1", "₂": "_2", "₃": "_3", "₄": "_4", "₅": "_5",
    "₆": "_6", "₇": "_7", "₈": "_8", "₉": "_9",
    "±": r"\pm ", "∓": r"\mp ", "×": r"\times ", "÷": r"\div ",
    "−": "-", "→": r"\to ", "⇒": r"\Rightarrow ", "⇔": r"\Leftrightarrow ",
}
@dataclass
class MathValidation:
    valid: bool
    expression: str
    warnings: List[str] = field(default_factory=list)

def normalize_expression(expression: str) -> str:
    s=str(expression).strip()
    for old,new in UNICODE_MAP.items(): s=s.replace(old,new)
    for old,new in OPERATOR_MAP.items(): s=s.replace(old,new)
    s=s.replace(r"\operatorname",r"\mathrm").replace(r"\dfrac",r"\frac")
    s=re.sub(r"\\left\s*",r"\\left",s); s=re.sub(r"\\right\s*",r"\\right",s)
    s=re.sub(r"(?<![\\A-Za-z])det(?=\s*\()",r"\\mathrm{det}",s)
    s=re.sub(r"(?<![\\A-Za-z])tr(?=\s*\()",r"\\mathrm{tr}",s)
    s=re.sub(r"(?<![\\A-Za-z])rank(?=\s*\()",r"\\mathrm{rank}",s)
    s=re.sub(r"\blim\s*([A-Za-z])\s*->\s*([^\s]+)",r"\\lim_{\1\\to\2}",s)
    return s

def validate_expression(expression:str)->MathValidation:
    s=normalize_expression(expression); warnings=[]
    pairs=[("{","}"),("(",")"),("[","]")]
    for a,b in pairs:
        if s.count(a)!=s.count(b): warnings.append(f"Unbalanced {a}{b}")
    if s.count(r"\left")!=s.count(r"\right"): warnings.append("Unbalanced \\left / \\right")
    if s.count("$$")%2: warnings.append("Unbalanced display-math delimiters")
    residual=[c for c in "≤≥≠∞∂∇√∈∉∩∪⊂⊆⊃⊇πθλμσφωΔδ" if c in s]
    if residual: warnings.append("Unnormalized mathematical Unicode: "+", ".join(residual))
    return MathValidation(not warnings,s,warnings)
