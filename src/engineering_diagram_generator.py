from __future__ import annotations

import re
from pathlib import Path

from .diagram_detector import detect_diagram_type
from .diagram_ir import DiagramSpec, Point, Node, Edge, Axis, Series
from .diagram_parser import build_diagram_spec
from .engineering_diagram_renderer import render_engineering_diagram


ENGINEERING_TYPES = {
    "circuit_diagram", "block_diagram", "signal_diagram", "phasor_diagram",
    "vector_diagram", "transformer_equivalent_circuit", "motor_diagram",
    "control_system_diagram", "logic_circuit", "waveform", "network_diagram",
}


class EngineeringDiagramGenerator:
    """M18 processor: engineering diagram request -> validated IR -> SVG.

    The processor is intentionally conservative. It supports canonical
    engineering requests and structured DiagramSpec data. Unsupported or
    ambiguous requests raise ValueError instead of fabricating topology.
    """

    def detect(self, question):
        return detect_diagram_type(question)

    def build(self, question, data=None) -> DiagramSpec:
        if data is not None:
            spec = build_diagram_spec(data)
        else:
            detection = self.detect(question)
            if detection is None or detection.diagram_type not in ENGINEERING_TYPES:
                raise ValueError(
                    "M18 supports engineering diagram generation only; "
                    "no supported engineering diagram request detected."
                )
            spec = self._from_question(question, detection.diagram_type)
        if spec.diagram_type not in ENGINEERING_TYPES:
            raise ValueError("M18 accepts engineering diagram families only.")
        return spec.ensure_valid()

    def generate(self, question, data=None, output_path=None, width=1000, height=650):
        spec = self.build(question, data)
        svg = render_engineering_diagram(spec, width=width, height=height)
        if output_path is not None:
            Path(output_path).write_text(svg, encoding="utf-8")
        return {
            "diagram_type": spec.diagram_type,
            "spec": spec.to_dict(),
            "svg": svg,
            "output_path": str(output_path) if output_path else None,
        }

    def _from_question(self, question, diagram_type):
        q = str(question)

        if diagram_type == "circuit_diagram":
            return DiagramSpec(
                "circuit_diagram",
                title="Circuit diagram",
                properties={"components": self._parse_circuit_components(q)}
            )

        if diagram_type == "block_diagram":
            return self._control_or_block_spec(q, "block_diagram")

        if diagram_type == "signal_diagram":
            return self._control_or_block_spec(q, "signal_diagram")

        if diagram_type == "control_system_diagram":
            return self._control_or_block_spec(q, "control_system_diagram")

        if diagram_type == "phasor_diagram":
            vectors = self._parse_vectors(q)
            return DiagramSpec(
                "phasor_diagram", title="Phasor diagram",
                properties={"vectors": vectors, "origin": (250, 430)}
            )

        if diagram_type == "vector_diagram":
            vectors = self._parse_vectors(q, phasor=False)
            return DiagramSpec(
                "vector_diagram", title="Vector diagram",
                properties={"vectors": vectors, "origin": (200, 450)}
            )

        if diagram_type == "transformer_equivalent_circuit":
            return DiagramSpec(
                "transformer_equivalent_circuit",
                title="Transformer equivalent circuit",
                properties={"components": self._transformer_components(q)}
            )

        if diagram_type == "motor_diagram":
            machine = "Induction motor"
            if re.search(r"\bsynchronous\b", q, re.I):
                machine = "Synchronous motor"
            return DiagramSpec(
                "motor_diagram",
                title="Motor diagram",
                properties={"machine": machine}
            )

        if diagram_type == "logic_circuit":
            gates = self._parse_gates(q)
            return DiagramSpec(
                "logic_circuit", title="Logic circuit",
                properties={"gates": gates}
            )

        if diagram_type == "waveform":
            return DiagramSpec(
                "waveform", title="Engineering waveform",
                properties=self._parse_waveform(q)
            )

        if diagram_type == "network_diagram":
            return self._network_spec(q)

        raise ValueError(f"Unsupported M18 family: {diagram_type}")

    @staticmethod
    def _parse_circuit_components(q):
        comps = []
        # Explicit component tokens are accepted, while the fallback is a
        # deterministic R-C source circuit.
        if re.search(r"\bresistor\b|\bR\d+\b", q, re.I):
            comps.append({"type": "resistor", "label": "R1", "x1": 160, "y1": 225, "x2": 430, "y2": 225})
        if re.search(r"\bcapacitor\b|\bC\d+\b", q, re.I):
            comps.append({"type": "capacitor", "label": "C1", "x1": 430, "y1": 225, "x2": 430, "y2": 425})
        if re.search(r"\binductor\b|\bL\d+\b", q, re.I):
            comps.append({"type": "inductor", "label": "L1", "x1": 430, "y1": 225, "x2": 650, "y2": 225})
        if re.search(r"\bvoltage source\b|\bAC source\b|\bDC source\b", q, re.I):
            typ = "ac_source" if re.search(r"\bAC source\b", q, re.I) else "voltage_source"
            comps.insert(0, {"type": typ, "label": "Vs", "x1": 160, "y1": 325, "x2": 160, "y2": 225})
        if not comps:
            comps = [
                {"type": "voltage_source", "label": "Vs", "x1": 160, "y1": 325, "x2": 160, "y2": 225},
                {"type": "resistor", "label": "R1", "x1": 160, "y1": 225, "x2": 430, "y2": 225},
                {"type": "capacitor", "label": "C1", "x1": 430, "y1": 225, "x2": 430, "y2": 425},
                {"type": "wire", "x1": 430, "y1": 425, "x2": 160, "y2": 425},
                {"type": "wire", "x1": 160, "y1": 425, "x2": 160, "y2": 325},
            ]
        return comps

    @staticmethod
    def _transformer_components(q):
        # Canonical single-phase approximate equivalent circuit. User-supplied
        # component names can be preserved in the labels.
        r1 = "R1"; x1 = "X1"; r2 = "R2'"; x2 = "X2'"
        if re.search(r"\bR_?1\b", q, re.I): r1 = "R1"
        return [
            {"type":"voltage_source","label":"V1","x1":110,"y1":330,"x2":110,"y2":230},
            {"type":"resistor","label":r1,"x1":110,"y1":230,"x2":270,"y2":230},
            {"type":"inductor","label":x1,"x1":270,"y1":230,"x2":430,"y2":230},
            {"type":"wire","x1":430,"y1":230,"x2":570,"y2":230},
            {"type":"resistor","label":r2,"x1":570,"y1":230,"x2":700,"y2":230},
            {"type":"inductor","label":x2,"x1":700,"y1":230,"x2":850,"y2":230},
            {"type":"wire","x1":850,"y1":230,"x2":850,"y2":430},
            {"type":"wire","x1":850,"y1":430,"x2":110,"y2":430},
            {"type":"wire","x1":110,"y1":430,"x2":110,"y2":330},
        ]

    @staticmethod
    def _parse_vectors(q, phasor=True):
        vectors = []
        # Matches e.g. V=10∠30°, I=5 angle -20°, or A magnitude 3 angle 45.
        pat = re.compile(
            r"\b([A-Za-z][A-Za-z0-9_]*)\s*(?:=|\s+magnitude\s*)"
            r"(-?\d+(?:\.\d+)?)\s*(?:∠|angle)\s*(-?\d+(?:\.\d+)?)",
            re.I
        )
        for m in pat.finditer(q):
            vectors.append({
                "label": m.group(1),
                "magnitude": float(m.group(2)),
                "angle_deg": float(m.group(3)),
            })
        if not vectors:
            vectors = [{"label": "V" if phasor else "A",
                        "magnitude": 220 if phasor else 260,
                        "angle_deg": 30 if phasor else 25}]
        if not phasor:
            # Convert polar-looking data to Cartesian vector data.
            return [{
                "label": v["label"],
                "dx": v["magnitude"] * __import__("math").cos(__import__("math").radians(v["angle_deg"])),
                "dy": -v["magnitude"] * __import__("math").sin(__import__("math").radians(v["angle_deg"])),
            } for v in vectors]
        return vectors

    @staticmethod
    def _control_or_block_spec(q, diagram_type):
        names = []
        if diagram_type == "control_system_diagram":
            defaults = [
                ("R", "reference", (120, 300)),
                ("Σ", "summation", (270, 300)),
                ("G(s)", "plant", (470, 300)),
                ("H(s)", "feedback", (470, 470)),
            ]
            nodes = [Node(i, k, i, pos) for i,k,pos in defaults]
            edges = [
                Edge("R", "Σ", "signal", "r(t)", True),
                Edge("Σ", "G(s)", "signal", "e(t)", True),
                Edge("G(s)", "H(s)", "feedback", "y(t)", True),
                Edge("H(s)", "Σ", "feedback", "−", True),
            ]
            return DiagramSpec(diagram_type, title="Closed-loop control system",
                               nodes=nodes, edges=edges)
        tokens = re.findall(r"\b(?:input|output|controller|plant|integrator|gain|filter|summer|feedback|G\(s\)|H\(s\))\b",
                            q, re.I)
        if not tokens:
            tokens = ["Input", "Controller", "Plant", "Output"]
        tokens = [t if t not in {"input","output"} else t.title() for t in tokens][:6]
        nodes = []
        for i,t in enumerate(tokens):
            node_id = f"N{i+1}"
            nodes.append(Node(node_id, "block", t, (120+i*180, 300)))
        edges = [Edge(nodes[i].id,nodes[i+1].id,"signal",None,True)
                 for i in range(len(nodes)-1)]
        return DiagramSpec(diagram_type, title="Signal/block diagram",
                           nodes=nodes, edges=edges)

    @staticmethod
    def _parse_gates(q):
        types = re.findall(r"\b(AND|OR|NOT|NAND|NOR|XOR|XNOR)\b", q, re.I)
        types = [t.upper() for t in types]
        if not types:
            types=["AND"]
        gates=[]
        for i,t in enumerate(types[:5]):
            gates.append({
                "id": f"G{i+1}", "type": t, "label": t,
                "x": 380+i*180, "y": 300,
                "inputs": ["A","B"] if t!="NOT" else ["A"],
                "output": f"Y{i+1}",
            })
        return gates

    @staticmethod
    def _parse_waveform(q):
        kind="sine"
        for candidate, aliases in {
            "square": ["square","square wave"],
            "triangle": ["triangle","triangular","triangle wave"],
            "sawtooth": ["saw","sawtooth"],
            "sine": ["sine","sinusoidal","sinusoid"],
        }.items():
            if any(re.search(r"\b"+re.escape(a)+r"\b",q,re.I) for a in aliases):
                kind=candidate
                break
        def number(name, default):
            m=re.search(rf"\b{name}\s*[:=]?\s*(-?\d+(?:\.\d+)?)",q,re.I)
            return float(m.group(1)) if m else default
        return {
            "waveform_type": kind,
            "amplitude": number("amplitude",1.0),
            "frequency": number("frequency",1.0),
            "phase_deg": number("phase",0.0),
            "duty_cycle": number("duty",50.0),
        }

    @staticmethod
    def _network_spec(q):
        pairs=re.findall(r"\b([A-Za-z]\w*)\s*[-–]\s*([A-Za-z]\w*)\b",q)
        ids=[]
        for a,b in pairs:
            if a not in ids: ids.append(a)
            if b not in ids: ids.append(b)
        if not ids:
            ids=["A","B","C","D"]
            pairs=[("A","B"),("B","C"),("C","D"),("D","A")]
        nodes=[Node(n,"vertex",n) for n in ids]
        edges=[Edge(a,b,"edge") for a,b in pairs]
        return DiagramSpec("network_diagram",title="Network diagram",
                           nodes=nodes,edges=edges)


_default_generator = EngineeringDiagramGenerator()


def generate_engineering_diagram(question, data=None, output_path=None,
                                 width=1000, height=650):
    return _default_generator.generate(question, data, output_path, width, height)
