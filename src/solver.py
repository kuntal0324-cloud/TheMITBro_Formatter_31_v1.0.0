"""Independent verification utilities for Milestone 15."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional
try:
    import sympy as sp
    from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
    TRANS=standard_transformations+(convert_xor,implicit_multiplication_application)
except Exception:
    sp=None
    TRANS=()

@dataclass
class VerificationResult:
    status:str
    message:str
    details:dict=field(default_factory=dict)

def _clean(s):
    s=str(s).strip()
    s=s.replace("^","**").replace("√","sqrt")
    s=re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}",r"(\1)/(\2)",s)
    s=s.replace(r"\pi","pi").replace(r"\mathrm","")
    s=re.sub(r"(?<![A-Za-z])i(?![A-Za-z])","I",s)
    return s

def _parse(s):
    return parse_expr(_clean(s),transformations=TRANS,evaluate=True)

def verify_equality(lhs,rhs):
    if sp is None:return VerificationResult("UNKNOWN","SymPy is not installed.")
    try:
        a,b=_parse(lhs),_parse(rhs); d=sp.simplify(a-b)
        return VerificationResult("PASS" if d==0 else "FAIL",
            "Expressions are symbolically equal." if d==0 else "Expressions are not symbolically equal.",
            {"difference":str(d)})
    except Exception as exc:return VerificationResult("UNKNOWN","Expression could not be parsed.",{"error":str(exc)})

def verify_mcq_answer(options,answer_key,expected_value=None):
    key=answer_key.strip().upper()
    if key not in options:return VerificationResult("FAIL",f"Answer key '{key}' is not present.")
    if expected_value is None:return VerificationResult("UNKNOWN","No independently computed expected value supplied.")
    r=verify_equality(options[key],expected_value)
    r.details.update({"selected_option":key,"selected_value":options[key]})
    return r

def verify_process_result(result, expected=None):
    """Check a processor result against an independently supplied expected value."""
    if result.status not in ("SOLVED","VERIFIED"):
        return VerificationResult("UNKNOWN","Processor did not return a solved result.",{"status":result.status})
    if expected is None:return VerificationResult("UNKNOWN","No expected value supplied.")
    return verify_equality(str(result.result),str(expected))
