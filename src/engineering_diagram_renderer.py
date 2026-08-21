from __future__ import annotations

import math
import re
from typing import Iterable

from .diagram_ir import DiagramSpec, Node, Edge, Point
from .diagram_renderer import SVGCanvas, _esc, _num


ENGINEERING_TYPES = {
    "circuit_diagram", "block_diagram", "signal_diagram", "phasor_diagram",
    "vector_diagram", "transformer_equivalent_circuit", "motor_diagram",
    "control_system_diagram", "logic_circuit", "waveform", "network_diagram",
}


def _arrow(c: SVGCanvas, x1, y1, x2, y2, stroke="#333", width=1.8, size=8):
    c.line(x1, y1, x2, y2, stroke=stroke, stroke_width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    a = ang + math.pi * 0.82
    b = ang - math.pi * 0.82
    c.polygon(
        [(x2, y2), (x2 + size * math.cos(a), y2 + size * math.sin(a)),
         (x2 + size * math.cos(b), y2 + size * math.sin(b))],
        fill=stroke
    )


def _label(c, x, y, text, size=14, anchor="middle"):
    c.text(x, y, text, text_anchor=anchor, font_size=size, fill="#111")


def _node_positions(spec: DiagramSpec):
    out = {}
    for i, n in enumerate(spec.nodes):
        if n.position is not None:
            out[n.id] = (float(n.position[0]), float(n.position[1]))
        else:
            # Stable fallback layout: left-to-right rows.
            out[n.id] = (140 + (i % 4) * 190, 180 + (i // 4) * 150)
    return out


def _component_type(component):
    return str(component.get("type") or component.get("kind") or "wire").lower()


class EngineeringDiagramRenderer:
    """M18 deterministic SVG renderer for engineering diagram families."""

    SUPPORTED = ENGINEERING_TYPES

    def render(self, spec: DiagramSpec, width=1000, height=650):
        spec.ensure_valid()
        if spec.diagram_type not in self.SUPPORTED:
            raise ValueError(f"M18 does not generate '{spec.diagram_type}'.")
        c = SVGCanvas(width, height)
        title = spec.title or spec.diagram_type.replace("_", " ").title()
        getattr(self, f"_render_{spec.diagram_type}")(c, spec)
        return c.finish(title=title, description=f"TheMITbro M18 {spec.diagram_type} SVG")

    def _heading(self, c, spec, text=None):
        c.text(20, 28, text or spec.title or spec.diagram_type.replace("_", " ").title(),
               font_size=18, font_weight="600", fill="#111")

    def _render_circuit_diagram(self, c, spec):
        self._heading(c, spec, "Circuit diagram")
        comps = list(spec.properties.get("components", []))
        if not comps:
            comps = [
                {"type": "voltage_source", "label": "Vs", "x1": 160, "y1": 325, "x2": 160, "y2": 225},
                {"type": "resistor", "label": "R1", "x1": 160, "y1": 225, "x2": 430, "y2": 225},
                {"type": "capacitor", "label": "C1", "x1": 430, "y1": 225, "x2": 430, "y2": 425},
                {"type": "wire", "label": "", "x1": 430, "y1": 425, "x2": 160, "y2": 425},
                {"type": "wire", "label": "", "x1": 160, "y1": 425, "x2": 160, "y2": 325},
            ]
        for comp in comps:
            self._draw_component(c, comp)

    def _draw_component(self, c, comp):
        typ = _component_type(comp)
        x1, y1 = float(comp.get("x1", 100)), float(comp.get("y1", 300))
        x2, y2 = float(comp.get("x2", 300)), float(comp.get("y2", 300))
        label = str(comp.get("label") or comp.get("id") or comp.get("value") or "")
        dx, dy = x2-x1, y2-y1
        length = math.hypot(dx, dy) or 1
        ux, uy = dx/length, dy/length
        px, py = -uy, ux
        lead = min(45, length*0.22)
        sx, sy = x1 + ux*lead, y1 + uy*lead
        ex, ey = x2 - ux*lead, y2 - uy*lead
        c.line(x1, y1, sx, sy, stroke="#333", stroke_width=1.8)
        c.line(ex, ey, x2, y2, stroke="#333", stroke_width=1.8)

        if typ in {"wire", "conductor"}:
            c.line(sx, sy, ex, ey, stroke="#333", stroke_width=1.8)
        elif typ in {"resistor", "r"}:
            n=6; amp=9
            pts=[(sx,sy)]
            for i in range(1,n+1):
                t=i/n
                off=amp if i%2 else -amp
                pts.append((sx+ux*(length-2*lead)*t+px*off, sy+uy*(length-2*lead)*t+py*off))
            pts.append((ex,ey))
            c.polyline(pts, fill="none", stroke="#333", stroke_width=2)
        elif typ in {"capacitor", "c"}:
            cx, cy=(sx+ex)/2,(sy+ey)/2
            gap=10; half=16
            c.line(cx+px*gap+ux*half, cy+py*gap+uy*half,
                   cx+px*gap-ux*half, cy+py*gap-uy*half, stroke="#333", stroke_width=2)
            c.line(cx-px*gap+ux*half, cy-py*gap+uy*half,
                   cx-px*gap-ux*half, cy-py*gap-uy*half, stroke="#333", stroke_width=2)
        elif typ in {"inductor", "l"}:
            loops=4; radius=12
            pts=[]
            for i in range(41):
                t=i/40
                theta=math.pi*loops*t
                along=(length-2*lead)*t
                xx=sx+ux*along+px*math.sin(theta)*radius
                yy=sy+uy*along+py*math.sin(theta)*radius
                pts.append((xx,yy))
            c.polyline(pts, fill="none", stroke="#333", stroke_width=2)
        elif typ in {"voltage_source", "source", "ac_source", "dc_source"}:
            cx, cy=(sx+ex)/2,(sy+ey)/2
            c.circle(cx,cy,23,fill="white",stroke="#333",stroke_width=2)
            c.text(cx,cy+5,"~" if typ=="ac_source" else "+",text_anchor="middle",font_size=18,fill="#333")
        elif typ in {"current_source"}:
            cx, cy=(sx+ex)/2,(sy+ey)/2
            c.circle(cx,cy,23,fill="white",stroke="#333",stroke_width=2)
            _arrow(c,cx,cy+12,cx,cy-12,stroke="#333",width=1.5,size=6)
        else:
            c.rect(min(sx,ex),min(sy,ey),abs(ex-sx) or 28,abs(ey-sy) or 28,
                   fill="white",stroke="#333",stroke_width=2)
        if label:
            _label(c,(x1+x2)/2+px*25,(y1+y2)/2+py*25,label,13)

    def _render_block_diagram(self, c, spec):
        self._render_node_edge_system(c,spec,"Block diagram",directed=True,shape="block")

    def _render_signal_diagram(self, c, spec):
        self._render_node_edge_system(c,spec,"Signal-flow diagram",directed=True,shape="signal")

    def _render_control_system_diagram(self, c, spec):
        self._render_node_edge_system(c,spec,"Control-system diagram",directed=True,shape="block")
        # If no explicit feedback edge exists, draw the canonical feedback loop.
        if not spec.edges:
            pass

    def _render_network_diagram(self, c, spec):
        self._render_node_edge_system(c,spec,"Network diagram",directed=False,shape="network")

    def _render_node_edge_system(self,c,spec,title,directed=False,shape="block"):
        self._heading(c,spec,title)
        pos=_node_positions(spec)
        for e in spec.edges:
            if e.source not in pos or e.target not in pos: continue
            x1,y1=pos[e.source]; x2,y2=pos[e.target]
            if directed or e.directed:
                _arrow(c,x1,y1,x2,y2,stroke="#444")
            else:
                c.line(x1,y1,x2,y2,stroke="#555",stroke_width=1.8)
            if e.label:
                _label(c,(x1+x2)/2,(y1+y2)/2-8,e.label,12)
        for n in spec.nodes:
            x,y=pos[n.id]
            kind=str(n.kind).lower()
            if shape=="block" or kind in {"block","gain","plant","controller","summation","integrator"}:
                w=float(n.properties.get("width",120)); h=float(n.properties.get("height",55))
                if kind=="summation":
                    c.circle(x,y,25,fill="white",stroke="#333",stroke_width=2)
                    _label(c,x,y+5,n.label or n.id,15)
                else:
                    c.rect(x-w/2,y-h/2,w,h,fill="white",stroke="#333",stroke_width=2)
                    _label(c,x,y+5,n.label or n.id,14)
            elif shape=="network":
                c.circle(x,y,18,fill="white",stroke="#333",stroke_width=2)
                _label(c,x,y+5,n.label or n.id,13)
            else:
                c.circle(x,y,20,fill="white",stroke="#333",stroke_width=2)
                _label(c,x,y+5,n.label or n.id,13)

    def _render_phasor_diagram(self,c,spec):
        self._heading(c,spec,"Phasor diagram")
        origin=spec.properties.get("origin",(250,430))
        ox,oy=float(origin[0]),float(origin[1])
        vectors=spec.properties.get("vectors",[])
        if not vectors and spec.edges:
            vectors=[]
            for e in spec.edges:
                vectors.append({"label":e.label or e.target,"magnitude":float(e.properties.get("magnitude",150)),
                                 "angle_deg":float(e.properties.get("angle_deg",0))})
        if not vectors:
            vectors=[{"label":"V","magnitude":220,"angle_deg":30}]
        c.line(70,oy,850,oy,stroke="#888",stroke_width=1)
        c.line(ox,100,ox,560,stroke="#888",stroke_width=1)
        _label(c,850,oy-8,"Re",12,"end"); _label(c,ox+8,105,"Im",12,"start")
        for v in vectors:
            mag=float(v.get("magnitude",150)); a=math.radians(float(v.get("angle_deg",0)))
            x=ox+mag*math.cos(a); y=oy-mag*math.sin(a)
            _arrow(c,ox,oy,x,y,stroke="#333",width=2.2,size=10)
            _label(c,x+10,y-8,str(v.get("label","V")),14,"start")
        c.circle(ox,oy,4,fill="#333")

    def _render_vector_diagram(self,c,spec):
        self._heading(c,spec,"Vector diagram")
        origin=spec.properties.get("origin",(200,450))
        ox,oy=float(origin[0]),float(origin[1])
        vectors=spec.properties.get("vectors",[])
        if not vectors:
            for e in spec.edges:
                vectors.append({"label":e.label or e.target,
                                "dx":float(e.properties.get("dx",180)),
                                "dy":float(e.properties.get("dy",-80))})
        if not vectors:
            vectors=[{"label":"A","dx":260,"dy":-120}]
        c.line(70,oy,850,oy,stroke="#888",stroke_width=1)
        c.line(ox,80,ox,560,stroke="#888",stroke_width=1)
        for v in vectors:
            x=ox+float(v.get("dx",100)); y=oy+float(v.get("dy",-100))
            _arrow(c,ox,oy,x,y,stroke="#333",width=2.2,size=10)
            _label(c,x+10,y-8,str(v.get("label","A")),14,"start")

    def _render_transformer_equivalent_circuit(self,c,spec):
        self._heading(c,spec,"Transformer equivalent circuit")
        comps=spec.properties.get("components")
        if not comps:
            comps=[
                {"type":"voltage_source","label":"V1","x1":110,"y1":330,"x2":110,"y2":230},
                {"type":"resistor","label":"R1","x1":110,"y1":230,"x2":270,"y2":230},
                {"type":"inductor","label":"X1","x1":270,"y1":230,"x2":430,"y2":230},
                {"type":"wire","x1":430,"y1":230,"x2":570,"y2":230},
                {"type":"resistor","label":"R2'","x1":570,"y1":230,"x2":700,"y2":230},
                {"type":"inductor","label":"X2'","x1":700,"y1":230,"x2":850,"y2":230},
                {"type":"wire","x1":850,"y1":230,"x2":850,"y2":430},
                {"type":"wire","x1":850,"y1":430,"x2":110,"y2":430},
                {"type":"wire","x1":110,"y1":430,"x2":110,"y2":330},
            ]
        for comp in comps:self._draw_component(c,comp)
        # Shunt branch, represented explicitly for the standard equivalent circuit.
        c.line(430,230,430,320,stroke="#333",stroke_width=1.8)
        self._draw_component(c,{"type":"resistor","label":"Rc","x1":430,"y1":320,"x2":430,"y2":430})
        c.line(500,230,500,320,stroke="#333",stroke_width=1.8)
        self._draw_component(c,{"type":"inductor","label":"Xm","x1":500,"y1":320,"x2":500,"y2":430})

    def _render_motor_diagram(self,c,spec):
        self._heading(c,spec,"Motor diagram")
        cx,cy=500,330
        r1,r2=180,105
        c.circle(cx,cy,r1,fill="white",stroke="#333",stroke_width=2)
        c.circle(cx,cy,r2,fill="none",stroke="#333",stroke_width=2)
        c.text(cx,cy-r1-12,str(spec.properties.get("machine","Induction motor")),
               text_anchor="middle",font_size=15,font_weight="600",fill="#111")
        # Stator slots/coils.
        for i in range(12):
            a=2*math.pi*i/12
            x1=cx+(r1-20)*math.cos(a); y1=cy+(r1-20)*math.sin(a)
            x2=cx+(r1-5)*math.cos(a); y2=cy+(r1-5)*math.sin(a)
            c.line(x1,y1,x2,y2,stroke="#555",stroke_width=3)
        # Rotor bars.
        for i in range(8):
            a=2*math.pi*i/8
            x1=cx+(r2-15)*math.cos(a); y1=cy+(r2-15)*math.sin(a)
            x2=cx+(r2+15)*math.cos(a); y2=cy+(r2+15)*math.sin(a)
            c.line(x1,y1,x2,y2,stroke="#333",stroke_width=3)
        c.text(cx,cy+5,"Rotor",text_anchor="middle",font_size=14,fill="#111")
        c.text(cx,cy+r1+25,"Stator",text_anchor="middle",font_size=14,fill="#111")
        _arrow(c,cx+r1+35,cy,cx+r1+95,cy,stroke="#333",width=2,size=9)
        c.text(cx+r1+100,cy-8,"ωm",font_size=14,fill="#111")

    def _render_logic_circuit(self,c,spec):
        self._heading(c,spec,"Logic circuit")
        gates=list(spec.properties.get("gates",[]))
        if not gates:
            gates=[
                {"id":"G1","type":"AND","label":"AND","x":400,"y":260,"inputs":["A","B"],"output":"Y"},
            ]
        # Draw input wires and gates deterministically.
        for g in gates:
            x=float(g.get("x",400)); y=float(g.get("y",300))
            typ=str(g.get("type","AND")).upper()
            inputs=list(g.get("inputs",["A","B"]))
            self._draw_gate(c,x,y,typ,str(g.get("label") or g.get("id") or typ))
            for i,name in enumerate(inputs):
                iy=y+(i-(len(inputs)-1)/2)*26
                c.line(x-150,iy,x-55,iy,stroke="#333",stroke_width=1.8)
                _label(c,x-160,iy+4,str(name),13,"end")
            c.line(x+55,y,x+150,y,stroke="#333",stroke_width=1.8)
            _label(c,x+160,y+4,str(g.get("output","Y")),13,"start")

    def _draw_gate(self,c,x,y,typ,label):
        w,h=110,70
        if typ=="NOT":
            c.polygon([(x-w/2,y-h/2),(x-w/2,y+h/2),(x+w/2,y)],fill="white",stroke="#333",stroke_width=2)
            c.circle(x+w/2+8,y,8,fill="white",stroke="#333",stroke_width=2)
        elif typ in {"AND","NAND"}:
            d=f"M {x-w/2:.1f} {y-h/2:.1f} L {x:.1f} {y-h/2:.1f} " \
              f"Q {x+w/2:.1f} {y:.1f} {x:.1f} {y+h/2:.1f} L {x-w/2:.1f} {y+h/2:.1f} Z"
            c.path(d,fill="white",stroke="#333",stroke_width=2)
            if typ=="NAND":c.circle(x+w/2+8,y,8,fill="white",stroke="#333",stroke_width=2)
        elif typ in {"OR","NOR","XOR","XNOR"}:
            d=f"M {x-w/2:.1f} {y-h/2:.1f} Q {x-5:.1f} {y-h/2:.1f} {x+w/2:.1f} {y:.1f} " \
              f"Q {x-5:.1f} {y+h/2:.1f} {x-w/2:.1f} {y+h/2:.1f} " \
              f"Q {x-15:.1f} {y:.1f} {x-w/2:.1f} {y-h/2:.1f} Z"
            c.path(d,fill="white",stroke="#333",stroke_width=2)
            if typ in {"NOR","XNOR"}:c.circle(x+w/2+8,y,8,fill="white",stroke="#333",stroke_width=2)
        else:
            c.rect(x-w/2,y-h/2,w,h,fill="white",stroke="#333",stroke_width=2)
        _label(c,x,y+5,typ,13)

    def _render_waveform(self,c,spec):
        self._heading(c,spec,"Engineering waveform")
        p=spec.properties
        amp=float(p.get("amplitude",1.0)); freq=float(p.get("frequency",1.0))
        phase=float(p.get("phase_deg",0.0)); kind=str(p.get("waveform_type") or "sine").lower()
        duty=float(p.get("duty_cycle",50.0))
        x0,y0=80,330; width,height=800,210
        c.line(x0,y0,x0+width,y0,stroke="#888",stroke_width=1)
        c.line(x0,y0-height/2,x0,y0+height/2,stroke="#888",stroke_width=1)
        pts=[]
        for i in range(401):
            t=i/400*2*math.pi*2
            if kind in {"square","square_wave"}:
                val=amp if (t/(2*math.pi) % 1) < duty/100 else -amp
            elif kind in {"saw","sawtooth"}:
                val=amp*(2*((t/(2*math.pi))%1)-1)
            elif kind in {"triangle","triangular"}:
                u=(t/(2*math.pi))%1
                val=amp*(4*abs(u-0.5)-1)
            else:
                val=amp*math.sin(freq*t+math.radians(phase))
            x=x0+width*i/400
            y=y0-(val/max(abs(amp),1e-9))*height/2
            pts.append((x,y))
        c.polyline(pts,fill="none",stroke="#333",stroke_width=2)
        _label(c,x0+width/2,570,f"{kind} waveform",14)

def render_engineering_diagram(spec: DiagramSpec, width=1000, height=650):
    return EngineeringDiagramRenderer().render(spec,width,height)


def save_engineering_diagram(spec: DiagramSpec, path, width=1000, height=650):
    svg=render_engineering_diagram(spec,width,height)
    with open(path,"w",encoding="utf-8") as fh: fh.write(svg)
    return str(path)
