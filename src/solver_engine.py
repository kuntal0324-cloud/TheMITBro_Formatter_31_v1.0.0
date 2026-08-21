"""Unified domain-routing engine for Milestone 15."""
from __future__ import annotations
import re
from .processor import PROCESSORS, ProcessResult

class SolverEngine:
    def __init__(self): self.processors=PROCESSORS

    def detect_domain(self, expression):
        s=str(expression).strip()
        l=s.lower()
        if re.search(r"\b(?:dy/dx|d[a-z]\s*/\s*d[a-z]|ode2)\b", l):
            return "differential_equation"
        if re.search(r"\b(?:laplace|inverse_laplace|fourier)\s*\(",l):
            return "transforms"
        if re.search(r"\b(?:det|determinant|trace|tr|rank|transpose|inverse|inv|eigenvals|eigenvectors|matrix)\s*\(",l) or re.search(r"\[\s*\[",s):
            return "matrix"
        if re.search(r"\b(?:conjugate|modulus|argument|arg|real|imaginary|abs|polar|rect)\s*\(",l) or re.search(r"(?<![A-Za-z])[ij](?![A-Za-z])",s):
            return "complex"
        if re.search(r"\b(?:gradient|grad|divergence|div|curl|dot|cross)\s*\(",l):
            return "vector_calculus"
        if re.search(r"\b(?:diff|derivative|partial|pdiff|total|totaldiff|mixed_partial|integrate|integral|double_integral|line_integral|surface_integral|limit|continuity|series|taylor|maclaurin)\s*\(",l):
            return "calculus"
        if re.search(r"\b(?:solve_trig|trig_solve)\s*\(",l) or re.search(r"\b(?:sin|cos|tan|cot|sec|csc)\b",l):
            return "trigonometry"
        if re.search(r"\b(?:solve_log|log_solve)\s*\(",l) or re.search(r"\blog\b",l):
            return "logarithm"
        if re.search(r"[∈∉∩∪⊂⊆⊃⊇]|\b(?:union|intersection|subset|complement)\b",s,re.I) or re.search(r"\}\s*[-\\∪∩]\s*\{",s):
            return "set_theory"
        if re.search(r"\b(?:prob|probability|binomial|combination)\s*\(",l) or re.search(r"\bP\s*\(",s):
            return "probability"
        if re.search(r"\b(?:mean|median|variance|std|stdev|mode|covariance|correlation)\s*\(",l):
            return "statistics"
        if re.search(r"\b(?:newton|bisection|euler|rk4|lagrange)\s*\(",l):
            return "numerical"
        return "algebra"

    def process(self, expression, domain=None):
        domain=domain or self.detect_domain(expression)
        p=self.processors.get(domain)
        if not p:return ProcessResult("UNKNOWN",domain,"",message="No processor registered for this domain.")
        return p.process(expression)
    solve=process

_default=SolverEngine()
def solve(expression,domain=None): return _default.process(expression,domain)
def detect_domain(expression): return _default.detect_domain(expression)
