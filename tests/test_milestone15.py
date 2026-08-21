from src.markdown_renderer import render_question, normalize_latex
from src.solver_engine import solve, detect_domain
from src.render_validator import render_is_valid
from src.solver import verify_equality

def test_render_operatorname():
    assert normalize_latex(r"\operatorname{tr}(A)") == r"\mathrm{tr}(A)"

def test_render_matrix():
    out=render_question("A =\n[ 1  2 ]\n[ 3  4 ]")
    assert r"\begin{bmatrix}1 & 2 \\ 3 & 4\end{bmatrix}" in out

def test_render_preserves_prose():
    out=render_question("For z = 2 + 3i, find |z|.")
    assert out.startswith("For ")
    assert "$For" not in out
    assert "$z = 2 + 3i, find |z|.$" in out

def test_render_inline_math_normalized():
    out=render_question(r"Value: $\operatorname{det}(A)=1$.")
    assert r"\operatorname" not in out
    assert r"\mathrm{det}" in out

def test_render_validation():
    assert render_is_valid(r"A=\operatorname{det}(B)")

# Matrix
def test_matrix_det(): assert solve("det([[1,2],[3,4]])").result=="-2"
def test_matrix_trace(): assert solve("trace([[1,2],[3,4]])").result=="5"
def test_matrix_rank(): assert solve("rank([[1,2],[2,4]])").result==1
def test_matrix_inverse(): assert solve("inverse([[1,2],[3,4]])").result==[["-2","1"],["3/2","-1/2"]]
def test_matrix_transpose(): assert solve("transpose([[1,2],[3,4]])").result==[["1","3"],["2","4"]]
def test_matrix_power(): assert solve("matrix([[1,2],[3,4]])^2").result==[["7","10"],["15","22"]]
def test_matrix_multiply(): assert solve("matrix([[1,2]])*matrix([[3],[4]])").result==[["11"]]
def test_matrix_add(): assert solve("matrix([[1,2]])+matrix([[3,4]])").result==[["4","6"]]
def test_matrix_eigenvalues(): assert solve("eigenvals([[2,0],[0,3]])").result=={"2":1,"3":1}
def test_matrix_singular_inverse():
    assert solve("inverse([[1,2],[2,4]])").status=="ERROR"

# Complex
def test_complex_components():
    r=solve("2+3i",domain="complex")
    assert r.result["real"]=="2" and r.result["imaginary"]=="3"
    assert r.result["modulus"]=="sqrt(13)"
def test_complex_conjugate(): assert solve("conjugate(2+3i)").result=="2 - 3*I"
def test_complex_argument(): assert str(solve("argument(-1)").result)=="pi"
def test_complex_modulus(): assert solve("modulus(3+4i)").result=="5"

# Algebra
def test_algebra_equation():
    assert solve("x^2-5*x+6=0").result==[{"x":"2"},{"x":"3"}]
def test_algebra_inequality(): assert solve("x^2-1>0").status=="SOLVED"
def test_algebra_factor(): assert solve("factor(x^2-5*x+6)").result=="(x - 3)*(x - 2)"
def test_algebra_expand(): assert solve("expand((x+1)^3)").result=="x**3 + 3*x**2 + 3*x + 1"

# Trig/log
def test_trig_simplify(): assert solve("sin(x)^2+cos(x)^2").result=="1"
def test_log_simplify(): assert solve("log(x*y)").status=="SOLVED"

# Calculus
def test_derivative(): assert solve("diff(x^3,x)").result=="3*x**2"
def test_higher_derivative(): assert solve("diff(x^4,x,2)").result=="12*x**2"
def test_partial_derivative(): assert solve("partial(x^2*y+y^3,x)").result=="2*x*y"
def test_indefinite_integral(): assert solve("integral(x^2,x)").result=="x**3/3"
def test_definite_integral(): assert solve("integral(x^2,x,0,1)").result=="1/3"
def test_limit(): assert solve("limit(sin(x)/x,x,0)").result=="1"
def test_continuity(): assert solve("continuity(x^2,x,1)").result is True
def test_double_integral(): assert solve("double_integral(x+y,x,0,1,y,0,1)").result=="1"
def test_series(): assert solve("series(exp(x),x,0,4)").status=="SOLVED"

# Differential equations/transforms
def test_ode(): assert solve("dy/dx=y").status=="SOLVED"
def test_laplace(): assert solve("laplace(exp(-x),x,s)").result=="1/(s + 1)"
def test_inverse_laplace(): assert solve("inverse_laplace(1/(s+1),t,s)").result=="exp(-t)"

# Sets/probability/statistics
def test_set_intersection(): assert solve("{1,2,3} ∩ {2,3,4}").result==["2","3"]
def test_set_union(): assert solve("{1,2} ∪ {2,3}").result==["1","2","3"]
def test_set_difference(): assert solve("{1,2,3} - {2}").result==["1","3"]
def test_subset(): assert solve("subset({1,2},{1,2,3})").result is True
def test_probability_rational(): assert solve("P(A)=3/10").result=="3/10"
def test_combination(): assert solve("combination(5,2)").result=="10"
def test_binomial(): assert solve("binomial(4,1,0.5)").result=="1/4"
def test_statistics_mean(): assert solve("mean(1,2,3,4)").result==2.5
def test_statistics_median(): assert solve("median(1,2,4,10)").result==3.0
def test_statistics_variance(): assert abs(solve("variance(1,2,3)").result-(2/3))<1e-12

# Vector calculus
def test_gradient(): assert solve("gradient(x^2+y^2,x,y)").result==["2*x","2*y"]
def test_divergence(): assert solve("divergence((x,y,z),x,y,z)").result=="3"
def test_curl(): assert solve("curl((-y,x,0),x,y,z)").result==["0","0","2"]
def test_dot(): assert solve("dot([1,2,3],[4,5,6])").result=="32"
def test_cross(): assert solve("cross([1,0,0],[0,1,0])").result==["0","0","1"]

# Numerical
def test_newton():
    r=solve("newton(x^2-2,x,1,5)")
    assert abs(float(r.result)-2**0.5)<1e-10
def test_bisection():
    r=solve("bisection(x^2-2,x,0,2,40)")
    assert abs(float(r.result)-2**0.5)<1e-10

# Routing
def test_domain_routing():
    cases={
        "det([[1,2],[3,4]])":"matrix",
        "2+3i":"complex",
        "x^2=4":"algebra",
        "sin(x)^2":"trigonometry",
        "log(x)":"logarithm",
        "diff(x^2,x)":"calculus",
        "dy/dx=y":"differential_equation",
        "laplace(exp(-x),x,s)":"transforms",
        "{1,2} ∪ {2,3}":"set_theory",
        "P(A)=3/10":"probability",
        "mean(1,2,3)":"statistics",
        "gradient(x^2+y^2,x,y)":"vector_calculus",
        "newton(x^2-2,x,1,4)":"numerical",
    }
    for expression,domain in cases.items(): assert detect_domain(expression)==domain

# Verification
def test_verification():
    assert verify_equality("1/2+1/2","1").status=="PASS"
    assert verify_equality("1/2","2").status=="FAIL"

def test_mixed_matrix_expression():
    assert solve("trace(matrix([[1,2],[3,4]])*matrix([[5,6],[7,8]]))").result=="69"

def test_total_derivative():
    assert solve("total(x^2+y^2,x,2*t,y,3*t,t)").result=="26*t"

def test_mixed_partial():
    assert solve("mixed_partial(x^2*y,x,y)").result=="2*x"

def test_line_integral():
    assert solve("line_integral(y,x,x,y,t,0,1,t,t)").result=="1"

def test_surface_integral():
    assert solve("surface_integral(1,x,y,z,u,v,0,1,0,1,u,v,0)").result=="1"

def test_trig_equation():
    assert solve("sin(x)=0",domain="trigonometry").status=="SOLVED"

def test_log_equation():
    assert solve("log(x)=1",domain="logarithm").status=="SOLVED"

def test_fourier():
    assert solve("fourier(exp(-x**2),x)").status=="SOLVED"

def test_complex_polar():
    r=solve("polar(1+i)")
    assert r.status=="SOLVED" and r.result["modulus"]=="sqrt(2)"

def test_complex_rect():
    assert solve("rect(2,0)").result=="2"

def test_statistics_correlation():
    assert abs(solve("correlation([1,2,3],[1,2,3])").result-1)<1e-12

def test_euler():
    r=solve("euler(x+y,x,y,0,1,0.1,1)")
    assert r.status=="SOLVED"

def test_rk4():
    r=solve("rk4(y,x,y,0,1,0.1,1)")
    assert r.status=="SOLVED"

def test_lagrange():
    assert solve("lagrange([0,1,2],[0,1,4],1.5)").result=="9/4"
