from __future__ import annotations
from dataclasses import dataclass
import re
from .markdown_renderer import render_question
from .math_normalizer import validate_expression

@dataclass
class RenderCheck:
    name:str
    passed:bool
    message:str
    output:str=""

def validate_rendered_markdown(text):
    output=render_question(text); checks=[]
    checks.append(RenderCheck("latex_delimiters",output.count("$$")%2==0,"Display delimiters balanced.",output))
    checks.append(RenderCheck("operator_normalization",r"\operatorname" not in output,"Legacy operatorname removed.",output))
    valid=True
    for block in re.findall(r"\$\$(.*?)\$\$",output,re.S):
        if not validate_expression(block).valid: valid=False; break
    checks.append(RenderCheck("display_math_validation",valid,"Display math passes structural validation.",output))
    return checks

def render_is_valid(text): return all(c.passed for c in validate_rendered_markdown(text))
