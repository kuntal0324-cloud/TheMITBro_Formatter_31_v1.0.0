from __future__ import annotations

import html
import math
import re
from dataclasses import dataclass
from typing import Iterable, Sequence

from .diagram_ir import DiagramSpec, Point, Series


def _esc(value) -> str:
    return html.escape(str(value), quote=True)


def _num(value, default=0.0) -> float:
    try:
        x = float(value)
        return x if math.isfinite(x) else float(default)
    except Exception:
        return float(default)


@dataclass(frozen=True)
class Viewport:
    width: int
    height: int
    margin: float = 55.0


class SVGCanvas:
    """Small deterministic SVG backend used by M17.

    It deliberately emits plain SVG instead of relying on a GUI/backend. This
    makes generated diagrams portable to Markdown/HTML/PDF pipelines later.
    """

    def __init__(self, width=900, height=600, background="white"):
        self.v = Viewport(int(width), int(height))
        self.background = background
        self.body: list[str] = []

    def line(self, x1, y1, x2, y2, **attrs):
        a = " ".join(f'{k.replace("_","-")}="{_esc(v)}"' for k, v in attrs.items())
        self.body.append(f'<line x1="{_num(x1):.3f}" y1="{_num(y1):.3f}" '
                         f'x2="{_num(x2):.3f}" y2="{_num(y2):.3f}" {a}/>')

    def polyline(self, points: Sequence[tuple[float, float]], **attrs):
        if len(points) < 2:
            return
        pts = " ".join(f"{_num(x):.3f},{_num(y):.3f}" for x, y in points)
        a = " ".join(f'{k.replace("_","-")}="{_esc(v)}"' for k, v in attrs.items())
        self.body.append(f'<polyline points="{pts}" {a}/>')

    def polygon(self, points: Sequence[tuple[float, float]], **attrs):
        if len(points) < 3:
            return
        pts = " ".join(f"{_num(x):.3f},{_num(y):.3f}" for x, y in points)
        a = " ".join(f'{k.replace("_","-")}="{_esc(v)}"' for k, v in attrs.items())
        self.body.append(f'<polygon points="{pts}" {a}/>')

    def circle(self, cx, cy, r, **attrs):
        a = " ".join(f'{k.replace("_","-")}="{_esc(v)}"' for k, v in attrs.items())
        self.body.append(f'<circle cx="{_num(cx):.3f}" cy="{_num(cy):.3f}" '
                         f'r="{_num(r):.3f}" {a}/>')

    def rect(self, x, y, w, h, **attrs):
        a = " ".join(f'{k.replace("_","-")}="{_esc(v)}"' for k, v in attrs.items())
        self.body.append(f'<rect x="{_num(x):.3f}" y="{_num(y):.3f}" '
                         f'width="{_num(w):.3f}" height="{_num(h):.3f}" {a}/>')

    def path(self, d, **attrs):
        a = " ".join(f'{k.replace("_","-")}="{_esc(v)}"' for k, v in attrs.items())
        self.body.append(f'<path d="{_esc(d)}" {a}/>')

    def text(self, x, y, value, **attrs):
        a = " ".join(f'{k.replace("_","-")}="{_esc(v)}"' for k, v in attrs.items())
        self.body.append(f'<text x="{_num(x):.3f}" y="{_num(y):.3f}" {a}>{_esc(value)}</text>')

    def finish(self, title=None, description=None) -> str:
        title_xml = f"<title>{_esc(title)}</title>" if title else ""
        desc_xml = f"<desc>{_esc(description)}</desc>" if description else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {self.v.width} {self.v.height}" '
            f'width="{self.v.width}" height="{self.v.height}" '
            f'role="img" aria-label="{_esc(title or "Mathematical diagram")}">'
            f"{title_xml}{desc_xml}"
            f'<rect x="0" y="0" width="100%" height="100%" fill="{_esc(self.background)}"/>'
            + "".join(self.body) + "</svg>"
        )


def _bounds(spec: DiagramSpec):
    xs, ys = [], []
    for p in spec.points:
        xs.append(_num(p.x)); ys.append(_num(p.y))
    for s in spec.series:
        for p in s.points:
            xs.append(_num(p.x)); ys.append(_num(p.y))
    if not xs:
        return (-5.0, 5.0, -5.0, 5.0)
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if xmin == xmax:
        xmin, xmax = xmin - 1, xmax + 1
    if ymin == ymax:
        ymin, ymax = ymin - 1, ymax + 1
    dx, dy = xmax - xmin, ymax - ymin
    pad_x, pad_y = max(0.5, 0.12 * dx), max(0.5, 0.12 * dy)
    return xmin - pad_x, xmax + pad_x, ymin - pad_y, ymax + pad_y


def _mapper(width, height, bounds, margin=55):
    xmin, xmax, ymin, ymax = bounds
    w, h = width - 2 * margin, height - 2 * margin

    def xy(x, y):
        px = margin + (float(x) - xmin) / (xmax - xmin) * w
        py = height - margin - (float(y) - ymin) / (ymax - ymin) * h
        return px, py

    return xy


def _axis_limits(spec: DiagramSpec, bounds):
    xmin, xmax, ymin, ymax = bounds
    amap = {a.name.lower(): a for a in spec.axes}
    if "x" in amap:
        if amap["x"].minimum is not None: xmin = float(amap["x"].minimum)
        if amap["x"].maximum is not None: xmax = float(amap["x"].maximum)
    if "y" in amap:
        if amap["y"].minimum is not None: ymin = float(amap["y"].minimum)
        if amap["y"].maximum is not None: ymax = float(amap["y"].maximum)
    return xmin, xmax, ymin, ymax


def draw_axes(c: SVGCanvas, spec: DiagramSpec, bounds, grid=True):
    xmin, xmax, ymin, ymax = _axis_limits(spec, bounds)
    xy = _mapper(c.v.width, c.v.height, (xmin, xmax, ymin, ymax), c.v.margin)
    x0, y0 = xy(0, 0)
    # Grid and ticks use an integer-friendly deterministic step.
    span = max(xmax - xmin, ymax - ymin)
    step = 1.0
    if span > 20: step = 5.0
    if span > 100: step = 10.0
    if grid:
        start = math.ceil(xmin / step) * step
        x = start
        while x <= xmax + 1e-9:
            px1, py1 = xy(x, ymin); px2, py2 = xy(x, ymax)
            c.line(px1, py1, px2, py2, stroke="#e6e6e6", stroke_width=1)
            x += step
        start = math.ceil(ymin / step) * step
        y = start
        while y <= ymax + 1e-9:
            px1, py1 = xy(xmin, y); px2, py2 = xy(xmax, y)
            c.line(px1, py1, px2, py2, stroke="#e6e6e6", stroke_width=1)
            y += step
    if xmin <= 0 <= xmax:
        c.line(x0, c.v.margin, x0, c.v.height-c.v.margin, stroke="#333", stroke_width=1.6)
    if ymin <= 0 <= ymax:
        c.line(c.v.margin, y0, c.v.width-c.v.margin, y0, stroke="#333", stroke_width=1.6)
    # Labels and small ticks.
    if ymin <= 0 <= ymax:
        c.text(c.v.width-c.v.margin+8, y0+4, "x", font_size=15, fill="#222")
    if xmin <= 0 <= xmax:
        c.text(x0+7, c.v.margin-10, "y", font_size=15, fill="#222")
    return xy, (xmin, xmax, ymin, ymax)


def _sample_function(expression: str, xmin=-5, xmax=5, count=300):
    """Sample a one-variable expression for an SVG polyline.

    SymPy is used only for parsing/evaluation; no image backend is required.
    Invalid/discontinuous samples split the curve instead of producing a
    misleading line across an asymptote.
    """
    try:
        import sympy as sp
        s = str(expression).strip()
        s = re.sub(r"^\s*[A-Za-z_]\w*\s*\(\s*x\s*\)\s*=\s*", "", s)
        s = re.sub(r"^\s*y\s*=\s*", "", s, flags=re.I)
        s = s.replace("^", "**").replace("√", "sqrt")
        x = sp.symbols("x")
        e = sp.sympify(s)
        fn = sp.lambdify(x, e, modules=["math"])
    except Exception:
        return []
    segments: list[list[tuple[float,float]]] = [[]]
    for i in range(count):
        xx = xmin + (xmax-xmin) * i / max(1, count-1)
        try:
            yy = float(fn(xx))
            if not math.isfinite(yy) or abs(yy) > 1e6:
                if segments[-1]: segments.append([])
                continue
            segments[-1].append((xx, yy))
        except Exception:
            if segments[-1]: segments.append([])
    return [s for s in segments if len(s) >= 2]


class MathematicalDiagramRenderer:
    """M17 renderer for the eight mathematical diagram families in M16."""

    SUPPORTED = {
        "coordinate_geometry", "graph", "geometric_figure",
        "probability_diagram", "venn_diagram", "function_plot",
        "number_line", "statistical_plot",
    }

    def render(self, spec: DiagramSpec, width=900, height=600) -> str:
        spec.ensure_valid()
        if spec.diagram_type not in self.SUPPORTED:
            raise ValueError(f"M17 does not generate '{spec.diagram_type}'. M18 owns engineering diagrams.")
        c = SVGCanvas(width, height)
        title = spec.title or spec.diagram_type.replace("_", " ").title()
        getattr(self, f"_render_{spec.diagram_type}")(c, spec)
        return c.finish(title=title, description=f"TheMITbro M17 {spec.diagram_type} SVG")

    def _render_coordinate_geometry(self, c, spec):
        bounds = _bounds(spec)
        xy, limits = draw_axes(c, spec, bounds, grid=True)
        for p in spec.points:
            x, y = xy(p.x, p.y)
            c.circle(x, y, 5, fill="#1f5eff")
            if p.label or p.id:
                c.text(x+8, y-8, p.label or p.id, font_size=14, fill="#111")
        for label in spec.labels:
            if label.position:
                x, y = xy(*label.position)
            else:
                target = next((p for p in spec.points if p.id == label.target), None)
                if target: x, y = xy(target.x, target.y)
                else: x, y = 60, 35
            c.text(x+6, y-6, label.text, font_size=14, fill="#111")
        c.text(20, 25, spec.title or "Coordinate geometry", font_size=18, font_weight="600", fill="#111")

    def _render_graph(self, c, spec):
        bounds = _bounds(spec)
        # Graphs are mathematical function plots with any explicitly supplied series.
        xy, limits = draw_axes(c, spec, bounds, grid=True)
        xmin, xmax, ymin, ymax = limits
        for expr in spec.expressions:
            for seg in _sample_function(expr, xmin, xmax):
                c.polyline([xy(x,y) for x,y in seg], fill="none", stroke="#1f5eff", stroke_width=2.2)
        for s in spec.series:
            pts=[xy(p.x,p.y) for p in s.points]
            if s.kind in ("scatter","points"):
                for x,y in pts: c.circle(x,y,4,fill="#d24b3f")
            else:
                c.polyline(pts,fill="none",stroke="#d24b3f",stroke_width=2)
        c.text(20,25,spec.title or "Graph",font_size=18,font_weight="600",fill="#111")

    def _render_function_plot(self, c, spec):
        self._render_graph(c, spec)

    def _render_geometric_figure(self, c, spec):
        c.text(20,25,spec.title or "Geometric figure",font_size=18,font_weight="600",fill="#111")
        pts=[(_num(p.x),_num(p.y)) for p in spec.points]
        if pts:
            xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
            bounds=(min(xs)-1,max(xs)+1,min(ys)-1,max(ys)+1)
            xy=_mapper(c.v.width,c.v.height,bounds,c.v.margin)
            mapped=[xy(*p) for p in pts]
            shape=str(spec.properties.get("shape","polygon")).lower()
            if shape=="circle":
                center=pts[0]
                radius=float(spec.properties.get("radius",1))
                edge=xy(center[0]+radius,center[1])
                c.circle(*xy(*center),abs(edge[0]-xy(*center)[0]),fill="none",stroke="#1f5eff",stroke_width=2.2)
            else:
                closed=bool(spec.properties.get("closed",True))
                c.polyline(mapped + ([mapped[0]] if closed and len(mapped)>2 else []),fill="none",stroke="#1f5eff",stroke_width=2.2)
            for p in spec.points:
                x,y=xy(p.x,p.y); c.circle(x,y,4,fill="#1f5eff")
                if p.label or p.id:c.text(x+7,y-7,p.label or p.id,font_size=13,fill="#111")
        else:
            # Explicit circle without points is still useful.
            r=float(spec.properties.get("radius",150))
            c.circle(c.v.width/2,c.v.height/2,r,fill="none",stroke="#1f5eff",stroke_width=2.2)

    def _render_probability_diagram(self, c, spec):
        c.text(20,25,spec.title or "Probability diagram",font_size=18,font_weight="600",fill="#111")
        positions={}
        for i,n in enumerate(spec.nodes):
            if n.position: positions[n.id]=n.position
            else:
                positions[n.id]=(120 + (i%4)*190, 120 + (i//4)*170)
        for e in spec.edges:
            if e.source not in positions or e.target not in positions: continue
            x1,y1=positions[e.source]; x2,y2=positions[e.target]
            c.line(x1,y1,x2,y2,stroke="#555",stroke_width=1.8)
            if e.label:
                c.text((x1+x2)/2+4,(y1+y2)/2-4,e.label,font_size=12,fill="#333")
        for n in spec.nodes:
            x,y=positions[n.id]; c.circle(x,y,24,fill="white",stroke="#1f5eff",stroke_width=2)
            c.text(x,y+5,n.label or n.id,text_anchor="middle",font_size=13,fill="#111")

    def _render_venn_diagram(self, c, spec):
        c.text(20,25,spec.title or "Venn diagram",font_size=18,font_weight="600",fill="#111")
        # M16 regions carry labels/properties; M17 renders a deterministic two/three-set view.
        groups=[]
        for r in spec.regions:
            group=r.properties.get("set") or r.properties.get("group")
            if group and group not in groups: groups.append(group)
        if not groups:
            groups=[r.id for r in spec.regions[:3]]
        groups=groups[:3] or ["A","B"]
        centers=[(330,310),(520,310),(425,220)]
        if len(groups)==2: centers=centers[:2]
        radius=150 if len(groups)==2 else 135
        for i,g in enumerate(groups):
            cx,cy=centers[i]
            c.circle(cx,cy,radius,fill="none",stroke="#1f5eff",stroke_width=2.5)
            c.text(cx,cy-radius-10,str(g),text_anchor="middle",font_size=16,font_weight="600",fill="#111")
        for r in spec.regions:
            label=r.label or r.id
            pos=r.properties.get("position")
            if pos and isinstance(pos,(list,tuple)) and len(pos)==2:
                c.text(float(pos[0]),float(pos[1]),label,font_size=13,text_anchor="middle",fill="#111")

    def _render_number_line(self, c, spec):
        c.text(20,25,spec.title or "Number line",font_size=18,font_weight="600",fill="#111")
        y=c.v.height/2; left,right=c.v.margin,c.v.width-c.v.margin
        c.line(left,y,right,y,stroke="#333",stroke_width=2)
        values=[p.x for p in spec.points] or [0]
        lo=min(values+[0])-1; hi=max(values+[0])+1
        if lo==hi:hi=lo+1
        def px(v):return left+(float(v)-lo)/(hi-lo)*(right-left)
        start=math.ceil(lo); end=math.floor(hi)
        for v in range(start,end+1):
            x=px(v); c.line(x,y-8,x,y+8,stroke="#333",stroke_width=1.4)
            c.text(x,y+28,str(v),text_anchor="middle",font_size=12,fill="#222")
        for p in spec.points:
            x=px(p.x); c.circle(x,y,6,fill="#1f5eff")
            if p.label or p.id:c.text(x,y-14,p.label or p.id,text_anchor="middle",font_size=13,fill="#111")

    def _render_statistical_plot(self, c, spec):
        c.text(20,25,spec.title or "Statistical plot",font_size=18,font_weight="600",fill="#111")
        series=spec.series
        if not series and spec.points:
            series=[Series(name="data",points=spec.points)]
        values=[]
        for s in series: values.extend(_num(v) for v in s.values)
        if not values:
            for s in series: values.extend(_num(p.y) for p in s.points)
        if not values: values=[0,1]
        kind=str(spec.properties.get("kind") or (series[0].kind if series else "scatter")).lower()
        if kind=="histogram":
            self._histogram(c,values)
        elif kind=="box":
            self._boxplot(c,values)
        else:
            self._stat_scatter(c,series)

    def _stat_scatter(self,c,series):
        allp=[]
        for i,s in enumerate(series):
            pts=s.points
            if not pts and s.values:
                pts=[Point(j,v) for j,v in enumerate(s.values)]
            allp.extend(pts)
        if not allp:return
        xs=[p.x for p in allp]; ys=[p.y for p in allp]
        xy=_mapper(c.v.width,c.v.height,(min(xs)-1,max(xs)+1,min(ys)-1,max(ys)+1),c.v.margin)
        for s in series:
            pts=s.points or [Point(j,v) for j,v in enumerate(s.values)]
            if s.kind=="line":
                c.polyline([xy(p.x,p.y) for p in pts],fill="none",stroke="#1f5eff",stroke_width=2)
            for p in pts:
                x,y=xy(p.x,p.y); c.circle(x,y,4,fill="#1f5eff")

    def _histogram(self,c,values):
        lo,hi=min(values),max(values)
        if lo==hi:hi=lo+1
        bins=max(3,min(10,int(math.sqrt(len(values)))+1))
        step=(hi-lo)/bins
        counts=[0]*bins
        for v in values:
            idx=min(bins-1,int((v-lo)/step)); counts[idx]+=1
        top=max(counts+[1])
        width=(c.v.width-2*c.v.margin)/bins
        for i,n in enumerate(counts):
            h=(c.v.height-2*c.v.margin)*n/top
            x=c.v.margin+i*width
            y=c.v.height-c.v.margin-h
            c.rect(x+1,y,width-2,h,fill="#d9e4ff",stroke="#1f5eff",stroke_width=1)

    def _boxplot(self,c,values):
        vals=sorted(values)
        q=lambda p: vals[int(round((len(vals)-1)*p))]
        mn,q1,med,q3,mx=q(0),q(.25),q(.5),q(.75),q(1)
        lo=min(vals); hi=max(vals) if max(vals)!=lo else lo+1
        xy=_mapper(c.v.width,c.v.height,(lo-1,hi+1,0,1),c.v.margin)
        x1,x2=xy(q1,.5)[0],xy(q3,.5)[0]
        xm=xy(med,.5)[0]; xa=xy(mn,.5)[0]; xb=xy(mx,.5)[0]; y= c.v.height/2
        c.line(xa,y,xb,y,stroke="#333",stroke_width=2)
        c.rect(x1,y-45,x2-x1,90,fill="#d9e4ff",stroke="#1f5eff",stroke_width=2)
        c.line(xm,y-45,xm,y+45,stroke="#1f5eff",stroke_width=2)
        c.line(xa,y-15,xa,y+15,stroke="#333",stroke_width=2); c.line(xb,y-15,xb,y+15,stroke="#333",stroke_width=2)


_default_renderer=MathematicalDiagramRenderer()


def render_diagram(spec: DiagramSpec, width=900, height=600) -> str:
    return _default_renderer.render(spec, width=width, height=height)


def save_diagram(spec: DiagramSpec, path, width=900, height=600) -> str:
    svg = render_diagram(spec, width=width, height=height)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return str(path)
