from __future__ import annotations

import re
from pathlib import Path

from .diagram_detector import detect_diagram_type
from .diagram_ir import DiagramSpec, Point, Series, Region, Axis, Node, Edge
from .diagram_parser import build_diagram_spec
from .diagram_renderer import render_diagram, save_diagram


MATHEMATICAL_TYPES = {
    "coordinate_geometry", "graph", "geometric_figure", "probability_diagram",
    "venn_diagram", "function_plot", "number_line", "statistical_plot",
}


def _float_pair(text):
    m = re.search(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)", text)
    return (float(m.group(1)), float(m.group(2))) if m else None


class MathematicalDiagramGenerator:
    """M17 processor: detected mathematical diagram -> validated IR -> SVG."""

    def detect(self, question):
        return detect_diagram_type(question)

    def build(self, question, data=None) -> DiagramSpec:
        if data is not None:
            spec = build_diagram_spec(data)
        else:
            detection = self.detect(question)
            if detection is None or detection.diagram_type not in MATHEMATICAL_TYPES:
                raise ValueError("M17 supports mathematical diagram generation only; no supported mathematical diagram request detected.")
            spec = self._from_question(question, detection.diagram_type)
        if spec.diagram_type not in MATHEMATICAL_TYPES:
            raise ValueError("M17 accepts mathematical diagram families only.")
        return spec.ensure_valid()

    def generate(self, question, data=None, output_path=None, width=900, height=600):
        spec = self.build(question, data)
        svg = render_diagram(spec, width=width, height=height)
        if output_path is not None:
            Path(output_path).write_text(svg, encoding="utf-8")
        return {"diagram_type": spec.diagram_type, "spec": spec.to_dict(),
                "svg": svg, "output_path": str(output_path) if output_path else None}

    def _from_question(self, question, diagram_type):
        q = str(question)
        title = None
        if diagram_type == "coordinate_geometry":
            pairs = re.findall(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)", q)
            points = []
            for i,(x,y) in enumerate(pairs):
                label = chr(65+i) if i < 26 else f"P{i+1}"
                points.append(Point(float(x),float(y),id=label,label=label))
            return DiagramSpec("coordinate_geometry", title="Coordinate geometry",
                               coordinate_system="cartesian",
                               points=points,
                               axes=[Axis("x",label="x",grid=True),Axis("y",label="y",grid=True)])
        if diagram_type in ("graph","function_plot"):
            exprs = []
            # Capture common y=f(x) / f(x)=... forms.
            for m in re.finditer(r"(?:y\s*=\s*|f\s*\(\s*x\s*\)\s*=\s*)([^.;\n]+)", q, re.I):
                exprs.append(m.group(1).strip())
            if not exprs:
                # A simple mathematical tail after "plot/graph".
                m = re.search(r"(?:plot|graph)\s+(.+)$", q, re.I)
                if m: exprs=[m.group(1).strip()]
            return DiagramSpec(diagram_type, title="Function plot" if diagram_type=="function_plot" else "Graph",
                               coordinate_system="cartesian", expressions=exprs or ["x"],
                               axes=[Axis("x",label="x",grid=True),Axis("y",label="y",grid=True)])
        if diagram_type == "geometric_figure":
            shape="triangle" if re.search(r"\btriangle\b",q,re.I) else "polygon"
            pairs=re.findall(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)",q)
            points=[Point(float(x),float(y),id=chr(65+i),label=chr(65+i)) for i,(x,y) in enumerate(pairs)]
            if not points and shape=="triangle":
                points=[Point(0,0,"A","A"),Point(4,0,"B","B"),Point(2,3,"C","C")]
            return DiagramSpec("geometric_figure",title=shape.title(),points=points,
                               properties={"shape":shape,"closed":True})
        if diagram_type == "venn_diagram":
            names=re.findall(r"\b(?:set|sets)\s+([A-Za-z])\b",q,re.I)
            names=names[:3] or ["A","B"]
            return DiagramSpec("venn_diagram",title="Venn diagram",
                               regions=[Region(n,"set",label=n,properties={"set":n}) for n in names])
        if diagram_type == "number_line":
            nums=re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?",q)
            pts=[Point(float(v),0,id=f"P{i+1}",label=v) for i,v in enumerate(nums[:12])]
            return DiagramSpec("number_line",title="Number line",points=pts)
        if diagram_type == "statistical_plot":
            nums=re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?",q)
            values=[float(v) for v in nums]
            kind="histogram" if re.search(r"\bhistogram\b",q,re.I) else "scatter"
            return DiagramSpec("statistical_plot",title="Statistical plot",
                               series=[Series(name="data",values=values,kind=kind)],
                               properties={"kind":kind})
        if diagram_type == "probability_diagram":
            return DiagramSpec(
                "probability_diagram", title="Probability diagram",
                nodes=[Node("S","root","S",(120,300)),
                       Node("A","event","A",(380,210)),
                       Node("B","event","B",(380,390))],
                edges=[Edge("S","A","branch","P(A)"), Edge("S","B","branch","P(B)")]
            )
        raise ValueError(f"Unsupported M17 family: {diagram_type}")


_default_generator = MathematicalDiagramGenerator()


def generate_mathematical_diagram(question, data=None, output_path=None, width=900, height=600):
    return _default_generator.generate(question, data, output_path, width, height)
