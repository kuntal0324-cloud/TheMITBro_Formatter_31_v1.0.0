"""Milestone 15 — domain processors.

The processors operate on a normalized mathematical representation and return a
uniform ProcessResult. They intentionally return UNKNOWN for syntax they cannot
interpret instead of guessing.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
import re
import math

try:
    import sympy as sp
    from sympy.parsing.sympy_parser import (
        parse_expr, standard_transformations, implicit_multiplication_application,
        convert_xor
    )
    SYMPY_AVAILABLE = True
except Exception:  # pragma: no cover
    SYMPY_AVAILABLE = False
    sp = None

TRANSFORMATIONS = (
    standard_transformations + (convert_xor, implicit_multiplication_application)
    if SYMPY_AVAILABLE else ()
)

@dataclass
class ProcessResult:
    status: str
    domain: str
    operation: str
    result: Any = None
    message: str = ""
    latex: Optional[str] = None
    details: dict = field(default_factory=dict)

def ok(domain, operation, result, message, obj=None, **details):
    return ProcessResult("SOLVED", domain, operation, result, message, latex(obj if obj is not None else result), details)

def unknown(domain, message, operation=""):
    return ProcessResult("UNKNOWN", domain, operation, message=message)

def error(domain, message, operation="", exc=None):
    d = {"error": str(exc)} if exc is not None else {}
    return ProcessResult("ERROR", domain, operation, message=message, details=d)

def clean(s: str) -> str:
    s = str(s).strip()
    s = s.replace("−", "-").replace("×", "*").replace("÷", "/").replace("·", "*")
    s = s.replace("∞", "oo")
    s = re.sub(r"\\left\s*|\\right\s*", "", s)
    s = re.sub(r"\\operatorname\{([^{}]+)\}", r"\1", s)
    s = re.sub(r"\\mathrm\{([^{}]+)\}", r"\1", s)
    s = re.sub(r"\\text\{([^{}]+)\}", r"\1", s)
    s = s.replace(r"\pi", "pi").replace(r"\theta", "theta")
    s = s.replace(r"\lambda", "lambda").replace(r"\alpha", "alpha")
    s = s.replace(r"\beta", "beta").replace(r"\gamma", "gamma")
    s = s.replace(r"\sin", "sin").replace(r"\cos", "cos").replace(r"\tan", "tan")
    s = s.replace(r"\cot", "cot").replace(r"\sec", "sec").replace(r"\csc", "csc")
    s = s.replace(r"\log", "log").replace(r"\ln", "log")
    s = re.sub(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", s)
    s = re.sub(r"\\(?:leq|le)", "<=", s).replace(r"\geq", ">=")
    s = s.replace(r"\neq", "!=")
    s = re.sub(r"\s+", " ", s)
    return s

def expr(s: str, local_dict=None):
    if not SYMPY_AVAILABLE:
        raise RuntimeError("SymPy unavailable")
    t = clean(s)
    # Common engineering/math notation.
    t = re.sub(r"(?<![A-Za-z])j(?![A-Za-z])", "I", t)
    return parse_expr(t, local_dict=local_dict or {}, transformations=TRANSFORMATIONS, evaluate=True)

def fmt(x):
    if SYMPY_AVAILABLE and isinstance(x, sp.MatrixBase):
        return [[fmt(x[i, j]) for j in range(x.cols)] for i in range(x.rows)]
    if isinstance(x, dict):
        return {str(k): fmt(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [fmt(v) for v in x]
    if SYMPY_AVAILABLE and isinstance(x, sp.Basic):
        return str(x)
    return x

def latex(x):
    if not SYMPY_AVAILABLE:
        return None
    try:
        return sp.latex(x)
    except Exception:
        return None

def matrix_from_literal(s: str):
    if not SYMPY_AVAILABLE:
        raise RuntimeError("SymPy unavailable")
    t = clean(s)
    m = re.fullmatch(r"\[\s*(.*)\s*\]", t)
    if not m:
        raise ValueError("Expected [[...],[...]] matrix literal")
    body = m.group(1).strip()
    rows_raw = re.findall(r"\[([^\[\]]*)\]", body)
    if not rows_raw:
        raise ValueError("Invalid matrix literal")
    rows = []
    for raw in rows_raw:
        vals = [v.strip() for v in raw.split(",") if v.strip()]
        if not vals:
            raise ValueError("Empty matrix row")
        rows.append([expr(v) for v in vals])
    if len({len(r) for r in rows}) != 1:
        raise ValueError("Matrix must be rectangular")
    return sp.Matrix(rows)

def _parse_linear_system(text):
    """Parse A*x=b or [[...]];[[...]] style systems."""
    m = re.fullmatch(r"\s*(\[\[.*\]\])\s*x\s*=\s*(\[\[.*\]\])\s*", clean(text), re.I)
    if m:
        return matrix_from_literal(m.group(1)), matrix_from_literal(m.group(2))
    return None


def split_args(text: str):
    """Split function arguments on commas at nesting depth zero."""
    out=[]; start=0; depth=0; quote=None
    for i,ch in enumerate(text):
        if quote:
            if ch==quote: quote=None
            continue
        if ch in "'\"": quote=ch; continue
        if ch in "([{": depth+=1
        elif ch in ")]}": depth-=1
        elif ch=="," and depth==0:
            out.append(text[start:i].strip()); start=i+1
    out.append(text[start:].strip())
    return out

def matrix_value(s: str):
    """Evaluate a restricted matrix expression recursively."""
    t=clean(s).strip()
    # Top-level + and * must be handled before the matrix(...) wrapper.
    for op in ("+", "*"):
        depth=0
        for i,ch in enumerate(t):
            if ch in "([{": depth+=1
            elif ch in ")]}": depth-=1
            elif ch==op and depth==0:
                A=matrix_value(t[:i]); B=matrix_value(t[i+1:])
                return A+B if op=="+" else A*B
    m=re.fullmatch(r"matrix\((.*)\)",t,re.I|re.S)
    if m: return matrix_value(m.group(1))
    if re.fullmatch(r"\[\[.*\]\]",t,re.S):
        return matrix_from_literal(t)
    m=re.fullmatch(r"(transpose|inverse|inv)\((.*)\)",t,re.I|re.S)
    if m:
        A=matrix_value(m.group(2))
        return A.T if m.group(1).lower()=="transpose" else A.inv()
    m=re.fullmatch(r"(.+)\s*(?:\*\*|\^)\s*(-?\d+)",t,re.S)
    if m: return matrix_value(m.group(1))**int(m.group(2))
    raise ValueError("Unsupported matrix expression")

class MatrixProcessor:
    @staticmethod
    def process(s):
        try:
            t = clean(s)
            # Nested matrix expressions permit mixed operations such as
            # trace(matrix(...)*matrix(...)) and det(matrix(...)^2).
            m_nested = re.fullmatch(r"(det|determinant|trace|tr|rank|transpose|inv|inverse)\((.+)\)", t, re.I|re.S)
            if m_nested and ("matrix(" in m_nested.group(2).lower() or "[[" in m_nested.group(2)):
                op,arg=m_nested.groups(); A=matrix_value(arg); op=op.lower()
                if op in ("det","determinant"): r=A.det(); operation="determinant"
                elif op in ("trace","tr"): r=A.trace(); operation="trace"
                elif op=="rank": r=A.rank(); operation="rank"
                elif op=="transpose": r=A.T; operation="transpose"
                else: r=A.inv(); operation="inverse"
                return ok("matrix",operation,fmt(r),f"{operation.title()} calculated.",r)
            sysm = _parse_linear_system(t)
            if sysm:
                A, b = sysm
                if A.rows != A.cols or b.cols != 1 or A.rows != b.rows:
                    return error("matrix", "Linear system dimensions are incompatible.", "solve")
                r = A.LUsolve(b)
                return ok("matrix", "solve", fmt(r), "Linear system solved.", r, shape=[A.rows, A.cols])

            m = re.fullmatch(r"(det|determinant|trace|tr|rank|transpose|inv|inverse|eigenvals|eigenvectors)\((.*)\)", t, re.I)
            if m:
                op, arg = m.groups()
                A = matrix_from_literal(arg)
                op = op.lower()
                if op in ("det", "determinant"):
                    if A.rows != A.cols: return error("matrix", "Determinant requires a square matrix.", "determinant")
                    r, operation = A.det(), "determinant"
                elif op in ("trace", "tr"):
                    if A.rows != A.cols: return error("matrix", "Trace requires a square matrix.", "trace")
                    r, operation = A.trace(), "trace"
                elif op == "rank": r, operation = A.rank(), "rank"
                elif op == "transpose": r, operation = A.T, "transpose"
                elif op in ("inv", "inverse"):
                    if A.rows != A.cols: return error("matrix", "Inverse requires a square matrix.", "inverse")
                    if A.det() == 0: return error("matrix", "Matrix is singular and has no inverse.", "inverse")
                    r, operation = A.inv(), "inverse"
                elif op == "eigenvals":
                    r, operation = A.eigenvals(), "eigenvalues"
                else:
                    r, operation = A.eigenvects(), "eigenvectors"
                return ok("matrix", operation, fmt(r), f"{operation.title()} calculated.", r, shape=[A.rows, A.cols])
            m = re.fullmatch(r"matrix\((\[\[.*\]\])\)\s*(?:\*\*|\^)\s*(-?\d+)", t, re.I)
            if m:
                A = matrix_from_literal(m.group(1)); n = int(m.group(2))
                if n < 0 and A.det() == 0: return error("matrix", "Negative matrix power requires an invertible matrix.", "power")
                r = A**n
                return ok("matrix", "power", fmt(r), "Matrix power calculated.", r, exponent=n)
            m = re.fullmatch(r"matrix\((\[\[.*\]\])\)\s*\+\s*matrix\((\[\[.*\]\])\)", t, re.I)
            if m:
                A, B = matrix_from_literal(m.group(1)), matrix_from_literal(m.group(2))
                if A.shape != B.shape: return error("matrix", "Matrix addition requires equal dimensions.", "addition")
                r = A+B; return ok("matrix", "addition", fmt(r), "Matrices added.", r)
            m = re.fullmatch(r"matrix\((\[\[.*\]\])\)\s*\*\s*matrix\((\[\[.*\]\])\)", t, re.I)
            if m:
                A, B = matrix_from_literal(m.group(1)), matrix_from_literal(m.group(2))
                if A.cols != B.rows: return error("matrix", "Inner matrix dimensions do not match.", "multiplication")
                r = A*B; return ok("matrix", "multiplication", fmt(r), "Matrices multiplied.", r)
            A = matrix_from_literal(t)
            return ok("matrix", "construct", fmt(A), "Matrix constructed.", A, shape=[A.rows,A.cols],
                      determinant=str(A.det()) if A.rows == A.cols else None)
        except Exception as exc:
            return error("matrix", "Matrix expression could not be processed.", exc=exc)

class ComplexProcessor:
    @staticmethod
    def process(s):
        try:
            t = clean(s)
            t = re.sub(r"(?<![A-Za-z])([ij])(?![A-Za-z])", "I", t)
            # Function-style requests.
            for name, func, operation in [
                ("polar", None, "polar"),
                ("rect", None, "rect"),
                ("conjugate", sp.conjugate if SYMPY_AVAILABLE else None, "conjugate"),
                ("modulus", sp.Abs if SYMPY_AVAILABLE else None, "modulus"),
                ("abs", sp.Abs if SYMPY_AVAILABLE else None, "modulus"),
                ("argument", sp.arg if SYMPY_AVAILABLE else None, "argument"),
                ("arg", sp.arg if SYMPY_AVAILABLE else None, "argument"),
                ("real", sp.re if SYMPY_AVAILABLE else None, "real"),
                ("imaginary", sp.im if SYMPY_AVAILABLE else None, "imaginary"),
            ]:
                m = re.fullmatch(rf"{name}\((.*)\)", t, re.I)
                if m:
                    eargs=split_args(m.group(1))
                    if name=="polar":
                        z=expr(eargs[0]); r=sp.Abs(z); a=sp.arg(z)
                        return ProcessResult("SOLVED","complex","polar",{"modulus":fmt(r),"argument":fmt(a)},
                                              "Polar representation calculated.",rf"r={latex(r)},\;\theta={latex(a)}")
                    if name=="rect":
                        r,theta=expr(eargs[0]),expr(eargs[1])
                        z=sp.simplify(r*(sp.cos(theta)+sp.I*sp.sin(theta)))
                        return ok("complex","rect",fmt(z),"Rectangular form calculated.",z)
                    e = expr(m.group(1))
                    r = sp.simplify(func(e))
                    return ok("complex", operation, fmt(r), f"Complex {operation} calculated.", r)
            e = expr(t)
            r = sp.simplify(e)
            data = {
                "simplified": fmt(r),
                "real": fmt(sp.simplify(sp.re(r))),
                "imaginary": fmt(sp.simplify(sp.im(r))),
                "modulus": fmt(sp.simplify(sp.Abs(r))),
                "argument": fmt(sp.simplify(sp.arg(r))),
                "conjugate": fmt(sp.simplify(sp.conjugate(r))),
            }
            return ok("complex", "evaluate", data, "Complex expression processed.", r, **data)
        except Exception as exc:
            return error("complex", "Complex expression could not be processed.", exc=exc)

class AlgebraProcessor:
    @staticmethod
    def process(s):
        try:
            t = clean(s)
            if re.search(r"(<=|>=|!=|<|>)", t):
                syms = sorted((expr(re.split(r"<=|>=|!=|<|>", t, maxsplit=1)[0]).free_symbols |
                               expr(re.split(r"<=|>=|!=|<|>", t, maxsplit=1)[1]).free_symbols), key=str)
                if len(syms) != 1:
                    return unknown("algebra", "Inequality solver currently requires one variable.", "inequality")
                r = sp.solve_univariate_inequality(expr(t), syms[0], relational=True)
                return ok("algebra", "inequality", fmt(r), "Inequality solved.", r)
            if re.search(r"=", t):
                lhs, rhs = re.split(r"=", t, maxsplit=1)
                L, R = expr(lhs), expr(rhs)
                vars_ = sorted(L.free_symbols | R.free_symbols, key=str)
                if not vars_:
                    same = sp.simplify(L-R) == 0
                    return ProcessResult("VERIFIED" if same else "FAIL", "algebra", "equality", bool(same),
                                         "Constant equality verified." if same else "Constant equality is false.",
                                         latex(sp.Eq(L,R)))
                sol = sp.solve(sp.Eq(L,R), vars_, dict=True)
                return ok("algebra", "equation", fmt(sol), "Equation solved.", sp.Eq(L,R),
                          variables=[str(v) for v in vars_])
            # Explicit operation wrappers.
            for name, fn in [("expand", sp.expand), ("factor", sp.factor), ("simplify", sp.simplify)]:
                m = re.fullmatch(rf"{name}\((.*)\)", t, re.I)
                if m:
                    r = fn(expr(m.group(1))); return ok("algebra", name, fmt(r), f"{name.title()} completed.", r)
            r = sp.simplify(expr(t))
            return ok("algebra", "simplify", fmt(r), "Algebraic expression simplified.", r)
        except Exception as exc:
            return error("algebra", "Algebraic expression could not be processed.", exc=exc)

class TrigonometryProcessor:
    @staticmethod
    def process(s):
        try:
            t=clean(s)
            m=re.fullmatch(r"(?:solve_trig|trig_solve)\((.*?),\s*([A-Za-z]\w*)\)",t,re.I)
            if m:
                e,v=m.groups(); x=sp.Symbol(v)
                if "=" in e:
                    lhs,rhs=e.split("=",1); target=expr(lhs)-expr(rhs)
                else: target=expr(e)
                r=sp.solveset(target,x,domain=sp.S.Reals)
                return ok("trigonometry","solve",fmt(r),"Trigonometric equation solved.",r)
            if "=" in t:
                lhs,rhs=t.split("=",1); x=sorted(expr(lhs).free_symbols|expr(rhs).free_symbols,key=str)
                if len(x)==1:
                    r=sp.solveset(expr(lhs)-expr(rhs),x[0],domain=sp.S.Reals)
                    return ok("trigonometry","solve",fmt(r),"Trigonometric equation solved.",r)
            r=sp.trigsimp(expr(t))
            return ok("trigonometry","simplify",fmt(r),"Trigonometric expression simplified.",r)
        except Exception as exc:return error("trigonometry","Trigonometric expression could not be processed.",exc=exc)

class LogarithmProcessor:
    @staticmethod
    def process(s):
        try:
            t=clean(s)
            m=re.fullmatch(r"(?:solve_log|log_solve)\((.*?),\s*([A-Za-z]\w*)\)",t,re.I)
            if m:
                e,v=m.groups(); x=sp.Symbol(v)
                target=expr(e.split("=",1)[0])-expr(e.split("=",1)[1]) if "=" in e else expr(e)
                r=sp.solveset(target,x,domain=sp.S.Reals)
                return ok("logarithm","solve",fmt(r),"Logarithmic equation solved.",r)
            if "=" in t:
                lhs,rhs=t.split("=",1); x=sorted(expr(lhs).free_symbols|expr(rhs).free_symbols,key=str)
                if len(x)==1:
                    r=sp.solveset(expr(lhs)-expr(rhs),x[0],domain=sp.S.Reals)
                    return ok("logarithm","solve",fmt(r),"Logarithmic equation solved.",r)
            r=sp.expand_log(expr(t),force=True)
            return ok("logarithm","simplify",fmt(r),"Logarithmic expression simplified.",r)
        except Exception as exc:return error("logarithm","Logarithmic expression could not be processed.",exc=exc)

class CalculusProcessor:
    @staticmethod
    def process(s):
        try:
            t=clean(s)
            m=re.fullmatch(r"(?:diff|derivative)\((.*?),\s*([A-Za-z]\w*)(?:,\s*(\d+))?\)",t,re.I)
            if m:
                f,v,n=m.groups(); x=sp.Symbol(v); r=sp.diff(expr(f),x,int(n or 1))
                return ok("calculus","derivative",fmt(r),"Derivative calculated.",r,order=int(n or 1))
            m=re.fullmatch(r"(?:partial|pdiff)\((.*?),\s*([A-Za-z]\w*)(?:,\s*(\d+))?\)",t,re.I)
            if m:
                f,v,n=m.groups(); x=sp.Symbol(v); r=sp.diff(expr(f),x,int(n or 1))
                return ok("calculus","partial_derivative",fmt(r),"Partial derivative calculated.",r,order=int(n or 1))
            m=re.fullmatch(r"mixed_partial\((.*?),\s*([A-Za-z]\w*),\s*([A-Za-z]\w*)\)",t,re.I)
            if m:
                f,xv,yv=m.groups(); x,y=sp.Symbol(xv),sp.Symbol(yv); r=sp.diff(expr(f),x,y)
                return ok("calculus","mixed_partial",fmt(r),"Mixed partial derivative calculated.",r)
            m=re.fullmatch(r"total\((.*)\)",t,re.I)
            if m:
                a=split_args(m.group(1))
                if len(a)<5:return unknown("calculus","Use total(f, x, dxdt, y, dydt) or total(f, x, x(t), y, y(t), t).","total_derivative")
                e=expr(a[0])
                if len(a)>=6 and len(a)%2==0:
                    path_var=a[-1]; pairs=a[1:-1]; result=0; substitutions={}
                    for i in range(0,len(pairs),2):
                        v=sp.Symbol(pairs[i]); path=expr(pairs[i+1]); substitutions[v]=path
                        result += sp.diff(e,v)*sp.diff(path,sp.Symbol(path_var))
                    result=sp.simplify(result.subs(substitutions))
                    return ok("calculus","total_derivative",fmt(result),"Total derivative along the supplied path calculated.",result)
                if (len(a)-1)%2:return unknown("calculus","Total derivative requires variable/derivative pairs.","total_derivative")
                result=sum(sp.diff(e,sp.Symbol(a[i]))*expr(a[i+1]) for i in range(1,len(a),2))
                return ok("calculus","total_derivative",fmt(sp.simplify(result)),"Total derivative calculated.",sp.simplify(result))
            m=re.fullmatch(r"(?:integrate|integral)\((.*?),\s*([A-Za-z]\w*)\)",t,re.I)
            if m:
                f,v=m.groups(); x=sp.Symbol(v); r=sp.integrate(expr(f),x)
                return ok("calculus","indefinite_integral",fmt(r),"Indefinite integral calculated.",r)
            m=re.fullmatch(r"(?:integrate|integral)\((.*?),\s*([A-Za-z]\w*),\s*([^,]+),\s*(.+)\)",t,re.I)
            if m:
                f,v,a,b=m.groups(); x=sp.Symbol(v); r=sp.integrate(expr(f),(x,expr(a),expr(b)))
                return ok("calculus","definite_integral",fmt(r),"Definite integral calculated.",r)
            m=re.fullmatch(r"double_integral\((.*?),\s*([A-Za-z]\w*),\s*([^,]+),\s*([^,]+),\s*([A-Za-z]\w*),\s*([^,]+),\s*(.+)\)",t,re.I)
            if m:
                f,xv,a,b,yv,c,d=m.groups(); x,y=sp.Symbol(xv),sp.Symbol(yv)
                r=sp.integrate(expr(f),(x,expr(a),expr(b)),(y,expr(c),expr(d)))
                return ok("calculus","double_integral",fmt(r),"Double integral calculated.",r)
            m=re.fullmatch(r"line_integral\((.*)\)",t,re.I)
            if m:
                a=split_args(m.group(1))
                if len(a)==9:
                    Fx,Fy,xv,yv,tv,lo,hi,xpath,ypath = a
                    x,y,u=sp.symbols(f"{xv} {yv} {tv}")
                    X,Y=expr(xpath),expr(ypath)
                    fieldx,fieldy=expr(Fx),expr(Fy)
                    integrand=fieldx.subs({x:X,y:Y})*sp.diff(X,u)+fieldy.subs({x:X,y:Y})*sp.diff(Y,u)
                    r=sp.integrate(integrand,(u,expr(lo),expr(hi)))
                    return ok("calculus","line_integral",fmt(r),"2-D line integral calculated.",r)
                return unknown("calculus","Use line_integral(Fx,Fy,x,y,t,a,b,x(t),y(t)).")
            m=re.fullmatch(r"surface_integral\((.*)\)",t,re.I)
            if m:
                a=split_args(m.group(1))
                if len(a)==13:
                    f,xv,yv,zv,uv,vv,a0,a1,b0,b1,Xs,Ys,Zs=a
                    x,y,z,u,v=sp.symbols(f"{xv} {yv} {zv} {uv} {vv}")
                    X,Y,Z=expr(Xs),expr(Ys),expr(Zs); field=expr(f)
                    ru=sp.Matrix([sp.diff(X,u),sp.diff(Y,u),sp.diff(Z,u)])
                    rv=sp.Matrix([sp.diff(X,v),sp.diff(Y,v),sp.diff(Z,v)])
                    jac=sp.sqrt(sum(q**2 for q in ru.cross(rv)))
                    integrand=field.subs({x:X,y:Y,z:Z})*jac
                    r=sp.integrate(integrand,(u,expr(a0),expr(a1)),(v,expr(b0),expr(b1)))
                    return ok("calculus","surface_integral",fmt(r),"Scalar surface integral calculated.",r)
                return unknown("calculus","Use surface_integral(f,x,y,z,u,v,a,b,c,d,X,Y,Z).")
            m=re.fullmatch(r"limit\((.*?),\s*([A-Za-z]\w*)\s*,\s*(.+)\)",t,re.I)
            if m:
                f,v,p=m.groups(); x=sp.Symbol(v); r=sp.limit(expr(f),x,expr(p))
                return ok("calculus","limit",fmt(r),"Limit calculated.",r)
            m=re.fullmatch(r"continuity\((.*?),\s*([A-Za-z]\w*)\s*,\s*(.+)\)",t,re.I)
            if m:
                f,v,p=m.groups(); x=sp.Symbol(v); e=expr(f); p0=expr(p)
                left,right=sp.limit(e,x,p0,dir="-"),sp.limit(e,x,p0,dir="+"); val=e.subs(x,p0)
                continuous=sp.simplify(left-right)==0 and sp.simplify(left-val)==0
                return ok("calculus","continuity",bool(continuous),"Continuity checked.",continuous,
                          left=fmt(left),right=fmt(right),value=fmt(val))
            m=re.fullmatch(r"(?:series|taylor|maclaurin)\((.*?),\s*([A-Za-z]\w*),\s*([^,]+),\s*(\d+)\)",t,re.I)
            if m:
                f,v,p,n=m.groups(); x=sp.Symbol(v); r=sp.series(expr(f),x,expr(p),int(n))
                return ok("calculus","series",str(r),"Series/Taylor expansion calculated.",r)
            return unknown("calculus","Recognized calculus syntax is not supported by this processor.")
        except Exception as exc: return error("calculus","Calculus expression could not be processed.",exc=exc)

class DifferentialEquationProcessor:
    @staticmethod
    def process(s):
        try:
            t=clean(s)
            # dy/dx = RHS
            m=re.fullmatch(r"d([A-Za-z])\s*/\s*d([A-Za-z])\s*=\s*(.+)",t)
            if m:
                yv,xv,rhs=m.groups(); x=sp.Symbol(xv); yf=sp.Function(yv); y=yf(x)
                rhs_expr=parse_expr(clean(rhs),local_dict={yv:y,xv:x},transformations=TRANSFORMATIONS,evaluate=True)
                sol=sp.dsolve(sp.Eq(sp.diff(y,x),rhs_expr))
                return ok("differential_equation","dsolve",str(sol),"First-order differential equation solved.",sol)
            m=re.fullmatch(r"ode2\((.*?),\s*(.*?),\s*([A-Za-z]\w*)\)",t,re.I)
            if m:
                lhs,rhs,xv=m.groups(); x=sp.Symbol(xv); yf=sp.Function("y"); y=yf(x)
                sol=sp.dsolve(sp.Eq(expr(lhs, {"y":y, xv:x}),expr(rhs, {"y":y, xv:x})))
                return ok("differential_equation","dsolve_second_order",str(sol),"Differential equation solved.",sol)
            return unknown("differential_equation","Use dy/dx = RHS or ode2(LHS, RHS, x).")
        except Exception as exc: return error("differential_equation","Differential equation could not be solved.",exc=exc)

class TransformProcessor:
    @staticmethod
    def process(s):
        try:
            t=clean(s)
            m=re.fullmatch(r"laplace\((.*?),\s*([A-Za-z]\w*),\s*([A-Za-z]\w*)\)",t,re.I)
            if m:
                f,v,q=m.groups(); r=sp.laplace_transform(expr(f),sp.Symbol(v),sp.Symbol(q),noconds=True)
                return ok("transforms","laplace",fmt(r),"Laplace transform calculated.",r)
            m=re.fullmatch(r"inverse_laplace\((.*?),\s*([A-Za-z]\w*),\s*([A-Za-z]\w*)\)",t,re.I)
            if m:
                F,tv,sv=m.groups(); r=sp.inverse_laplace_transform(expr(F),sp.Symbol(sv),sp.Symbol(tv))
                r=sp.simplify(r.replace(lambda z: z.func == sp.Heaviside, lambda z: sp.Integer(1)))
                return ok("transforms","inverse_laplace",fmt(r),"Inverse Laplace transform calculated for t>0.",r)
            m=re.fullmatch(r"fourier\((.*?),\s*([A-Za-z]\w*)\)",t,re.I)
            if m:
                f,v=m.groups(); x=sp.Symbol(v); r=sp.fourier_transform(expr(f),x,sp.Symbol("k"))
                return ok("transforms","fourier",fmt(r),"Fourier transform calculated.",r)
            return unknown("transforms","Use laplace(...), inverse_laplace(...), or fourier(...).")
        except Exception as exc: return error("transforms","Transform could not be processed.",exc=exc)

class SetProcessor:
    @staticmethod
    def _finite(text):
        return {sp.simplify(expr(v.strip())) for v in text.split(",") if v.strip()}
    @staticmethod
    def process(s):
        try:
            t=clean(s)
            m=re.fullmatch(r"\{([^{}]*)\}\s*([∩∪\\\-\+])\s*\{([^{}]*)\}",t)
            if m:
                a,op,b=m.groups(); A=SetProcessor._finite(a); B=SetProcessor._finite(b)
                if op=="∩": R=A&B; operation="intersection"
                elif op=="∪": R=A|B; operation="union"
                elif op in ("\\","-"): R=A-B; operation="difference"
                else: return unknown("set_theory","Unsupported set operation.")
                vals=sorted((str(v) for v in R), key=str)
                return ProcessResult("SOLVED","set_theory",operation,vals,"Finite set operation calculated.",
                                     r"\{" + ", ".join(vals) + r"\}")
            m=re.fullmatch(r"subset\((\{[^{}]*\}),\s*(\{[^{}]*\})\)",t,re.I)
            if m:
                A=SetProcessor._finite(m.group(1)[1:-1]); B=SetProcessor._finite(m.group(2)[1:-1])
                return ProcessResult("SOLVED","set_theory","subset",A <= B,"Subset relation checked.",
                                     r"A\subseteq B" if A <= B else r"A\not\subseteq B")
            return unknown("set_theory","Use finite sets with ∩, ∪, -, or subset(A,B).")
        except Exception as exc: return error("set_theory","Set expression could not be processed.",exc=exc)

class ProbabilityProcessor:
    @staticmethod
    def process(s):
        try:
            t=clean(s)
            m=re.fullmatch(r"(?:prob|probability)\((.*)\)",t,re.I)
            if m:
                r=sp.simplify(expr(m.group(1)))
                if r.is_real is False: return error("probability","Probability must be real.")
                return ok("probability","evaluate",fmt(r),"Probability expression evaluated.",r)
            m=re.fullmatch(r"P\(\s*([A-Za-z])\s*\)\s*=\s*(\d+)\s*/\s*(\d+)",t,re.I)
            if m:
                _,fav,total=m.groups(); fav,total=int(fav),int(total)
                if total<=0:return error("probability","Total outcomes must be positive.")
                if fav<0 or fav>total:return error("probability","Favourable outcomes must lie between 0 and total outcomes.")
                r=sp.Rational(fav,total); return ok("probability","probability",fmt(r),"Probability calculated.",r)
            m=re.fullmatch(r"binomial\((\d+),\s*(\d+),\s*(.*?)\)",t,re.I)
            if m:
                n,k,p=m.groups(); prob=sp.nsimplify(expr(p)); r=sp.binomial(int(n),int(k))*prob**int(k)*(1-prob)**(int(n)-int(k))
                return ok("probability","binomial",fmt(sp.simplify(r)),"Binomial probability calculated.",sp.simplify(r))
            m=re.fullmatch(r"combination\((\d+),\s*(\d+)\)",t,re.I)
            if m:
                r=sp.binomial(int(m.group(1)),int(m.group(2))); return ok("probability","combination",fmt(r),"Combination calculated.",r)
            return unknown("probability","Use prob(expression), P(A)=m/n, binomial(n,p,k), or combination(n,r).")
        except Exception as exc:return error("probability","Probability expression could not be processed.",exc=exc)

class StatisticsProcessor:
    @staticmethod
    def process(s):
        try:
            t=clean(s)
            m=re.fullmatch(r"(mean|median|variance|std|stdev|mode)\(([^)]*)\)",t,re.I)
            if m:
                op,data=m.groups(); vals=[float(x.strip()) for x in data.split(",") if x.strip()]
                if not vals:return error("statistics","Dataset is empty.",op)
                n=len(vals); mean=sum(vals)/n
                if op.lower()=="mean": r=mean
                elif op.lower()=="median":
                    z=sorted(vals); r=z[n//2] if n%2 else (z[n//2-1]+z[n//2])/2
                elif op.lower()=="variance": r=sum((x-mean)**2 for x in vals)/n
                elif op.lower() in ("std","stdev"): r=math.sqrt(sum((x-mean)**2 for x in vals)/n)
                else:
                    from collections import Counter
                    c=Counter(vals); mx=max(c.values()); r=sorted([v for v,k in c.items() if k==mx])
                return ProcessResult("SOLVED","statistics",op.lower(),r,"Statistic calculated.",str(r),{"n":n,"population_mean":mean})
            m=re.fullmatch(r"(covariance|correlation)\(([^)]*)\)",t,re.I)
            if m:
                op,data=m.groups(); parts=split_args(data)
                if len(parts)!=2:return error("statistics","Use covariance([x...],[y...]) or correlation([x...],[y...]).")
                X=[float(x) for x in parts[0].strip("[] ").split(",") if x.strip()]
                Y=[float(y) for y in parts[1].strip("[] ").split(",") if y.strip()]
                if len(X)!=len(Y) or not X:return error("statistics","Datasets must have equal nonzero length.")
                mx,my=sum(X)/len(X),sum(Y)/len(Y)
                cov=sum((x-mx)*(y-my) for x,y in zip(X,Y))/len(X)
                if op.lower()=="covariance": r=cov
                else:
                    den=math.sqrt(sum((x-mx)**2 for x in X)*sum((y-my)**2 for y in Y))
                    if den==0:return error("statistics","Correlation is undefined for a zero-variance dataset.")
                    r=sum((x-mx)*(y-my) for x,y in zip(X,Y))/den
                return ProcessResult("SOLVED","statistics",op.lower(),r,"Statistic calculated.",str(r))
            return unknown("statistics","Use mean, median, variance, std, mode, covariance, or correlation.")
        except Exception as exc:return error("statistics","Statistic could not be calculated.",exc=exc)

class VectorCalculusProcessor:
    @staticmethod
    def process(s):
        try:
            t=clean(s)
            m=re.fullmatch(r"gradient\((.*?),\s*([A-Za-z]\w*),\s*([A-Za-z]\w*)(?:,\s*([A-Za-z]\w*))?\)",t,re.I)
            if m:
                f,xv,yv,zv=m.groups(); vars_=[sp.Symbol(xv),sp.Symbol(yv)]+([sp.Symbol(zv)] if zv else [])
                r=sp.Matrix([sp.diff(expr(f),v) for v in vars_]); return ok("vector_calculus","gradient",[fmt(v) for v in r],"Gradient calculated.",r)
            m=re.fullmatch(r"divergence\(\((.*?),\s*(.*?),\s*(.*?)\),\s*([A-Za-z]\w*),\s*([A-Za-z]\w*),\s*([A-Za-z]\w*)\)",t,re.I)
            if m:
                fx,fy,fz,xv,yv,zv=m.groups(); x,y,z=sp.symbols(f"{xv} {yv} {zv}")
                r=sp.diff(expr(fx),x)+sp.diff(expr(fy),y)+sp.diff(expr(fz),z)
                return ok("vector_calculus","divergence",fmt(r),"Divergence calculated.",r)
            m=re.fullmatch(r"curl\(\((.*?),\s*(.*?),\s*(.*?)\),\s*([A-Za-z]\w*),\s*([A-Za-z]\w*),\s*([A-Za-z]\w*)\)",t,re.I)
            if m:
                fx,fy,fz,xv,yv,zv=m.groups(); x,y,z=sp.symbols(f"{xv} {yv} {zv}")
                F=[expr(fx),expr(fy),expr(fz)]
                r=sp.Matrix([sp.diff(F[2],y)-sp.diff(F[1],z), sp.diff(F[0],z)-sp.diff(F[2],x), sp.diff(F[1],x)-sp.diff(F[0],y)])
                return ok("vector_calculus","curl",[fmt(v) for v in list(r)],"Curl calculated.",r)
            m=re.fullmatch(r"(dot|cross)\(\[([^\]]*)\],\s*\[([^\]]*)\]\)",t,re.I)
            if m:
                op,a,b=m.groups()
                A=sp.Matrix([expr(x) for x in a.split(",")]); B=sp.Matrix([expr(x) for x in b.split(",")])
                r=A.dot(B) if op.lower()=="dot" else A.cross(B)
                return ok("vector_calculus",op.lower(),([fmt(v) for v in list(r)] if op.lower()=="cross" else fmt(r)),f"Vector {op.lower()} product calculated.",r)
            return unknown("vector_calculus","Use gradient, divergence, curl, dot, or cross.")
        except Exception as exc:return error("vector_calculus","Vector-calculus expression could not be processed.",exc=exc)

class NumericalProcessor:
    @staticmethod
    def process(s):
        try:
            t=clean(s)
            m=re.fullmatch(r"newton\((.*?),\s*([A-Za-z]\w*),\s*([^,]+),\s*(\d+)\)",t,re.I)
            if m:
                f,v,x0,n=m.groups(); x=sp.Symbol(v); fn=expr(f); xn=expr(x0); hist=[]; d=sp.diff(fn,x)
                for _ in range(int(n)):
                    den=d.subs(x,xn)
                    if den==0:return error("numerical","Newton iteration encountered zero derivative.","newton")
                    xn=sp.N(xn-fn.subs(x,xn)/den,15); hist.append(str(xn))
                return ProcessResult("SOLVED","numerical","newton",str(xn),"Newton iteration completed.",str(xn),{"iterations":hist})
            m=re.fullmatch(r"bisection\((.*?),\s*([A-Za-z]\w*),\s*([^,]+),\s*([^,]+),\s*(\d+)\)",t,re.I)
            if m:
                f,v,a,b,n=m.groups(); x=sp.Symbol(v); fn=expr(f); a=float(expr(a)); b=float(expr(b)); hist=[]
                fa=float(fn.subs(x,a)); fb=float(fn.subs(x,b))
                if fa*fb>0:return error("numerical","Bisection endpoints must bracket a root.","bisection")
                for _ in range(int(n)):
                    c=(a+b)/2; fc=float(fn.subs(x,c)); hist.append(c)
                    if abs(fc)<1e-14:a=b=c;break
                    if fa*fc<=0:b,fb=c,fc
                    else:a,fa=c,fc
                r=(a+b)/2
                return ProcessResult("SOLVED","numerical","bisection",r,"Bisection iteration completed.",str(r),{"iterations":hist})
            m=re.fullmatch(r"euler\((.*?),\s*([A-Za-z]\w*),\s*([A-Za-z]\w*),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*(\d+)\)",t,re.I)
            if m:
                f,xv,yv,x0,y0,h,n=m.groups(); x,y=sp.Symbol(xv),sp.Symbol(yv); X=float(expr(x0)); Y=float(expr(y0)); H=float(expr(h))
                fn=expr(f); hist=[(X,Y)]
                for _ in range(int(n)):
                    Y=Y+H*float(fn.subs({x:X,y:Y})); X=X+H; hist.append((X,Y))
                return ProcessResult("SOLVED","numerical","euler",Y,"Euler integration completed.",str(Y),{"trajectory":hist})
            m=re.fullmatch(r"rk4\((.*?),\s*([A-Za-z]\w*),\s*([A-Za-z]\w*),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*(\d+)\)",t,re.I)
            if m:
                f,xv,yv,x0,y0,h,n=m.groups(); x,y=sp.Symbol(xv),sp.Symbol(yv); X=float(expr(x0)); Y=float(expr(y0)); H=float(expr(h)); fn=expr(f); hist=[(X,Y)]
                for _ in range(int(n)):
                    k1=float(fn.subs({x:X,y:Y}))
                    k2=float(fn.subs({x:X+H/2,y:Y+H*k1/2}))
                    k3=float(fn.subs({x:X+H/2,y:Y+H*k2/2}))
                    k4=float(fn.subs({x:X+H,y:Y+H*k3}))
                    Y += H*(k1+2*k2+2*k3+k4)/6; X += H; hist.append((X,Y))
                return ProcessResult("SOLVED","numerical","rk4",Y,"Runge-Kutta 4 integration completed.",str(Y),{"trajectory":hist})
            m=re.fullmatch(r"lagrange\((\[[^\]]*\]),\s*(\[[^\]]*\]),\s*(.*)\)",t,re.I)
            if m:
                xs=[expr(v) for v in m.group(1).strip("[]").split(",")]; ys=[expr(v) for v in m.group(2).strip("[]").split(",")]
                if len(xs)!=len(ys):return error("numerical","Interpolation x/y datasets must have equal length.","lagrange")
                x0=sp.nsimplify(expr(m.group(3))); x=sp.Symbol("x")
                r=sum(ys[i]*sp.prod((x-xs[j])/(xs[i]-xs[j]) for j in range(len(xs)) if j!=i) for i in range(len(xs)))
                val=sp.simplify(r.subs(x,x0))
                return ok("numerical","lagrange",fmt(val),"Lagrange interpolation evaluated.",val)
            return unknown("numerical","Use newton, bisection, euler, rk4, or lagrange.")
        except Exception as exc:return error("numerical","Numerical method failed.",exc=exc)

PROCESSORS = {
    "matrix": MatrixProcessor,
    "complex": ComplexProcessor,
    "algebra": AlgebraProcessor,
    "trigonometry": TrigonometryProcessor,
    "logarithm": LogarithmProcessor,
    "calculus": CalculusProcessor,
    "differential_equation": DifferentialEquationProcessor,
    "transforms": TransformProcessor,
    "set_theory": SetProcessor,
    "probability": ProbabilityProcessor,
    "statistics": StatisticsProcessor,
    "vector_calculus": VectorCalculusProcessor,
    "numerical": NumericalProcessor,
}
