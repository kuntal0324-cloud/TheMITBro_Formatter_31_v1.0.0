from __future__ import annotations
from dataclasses import dataclass
import re
@dataclass(frozen=True)
class DiagramDetection:
    diagram_type:str; confidence:float; matched_terms:tuple[str,...]; reason:str
RULES=[("transformer_equivalent_circuit",.96,[r"\btransformer\b",r"\bequivalent circuit\b",r"\bR1\b",r"\bX1\b"]),("motor_diagram",.95,[r"\binduction motor\b",r"\bmotor diagram\b",r"\bstator\b",r"\brotor\b"]),("control_system_diagram",.95,[r"\bcontrol system\b",r"\bfeedback\b",r"\btransfer function\b"]),("logic_circuit",.95,[r"\blogic circuit\b",r"\bAND gate\b",r"\bOR gate\b",r"\bNOT gate\b",r"\bNAND\b",r"\bNOR\b"]),("circuit_diagram",.94,[r"\bcircuit diagram\b",r"\bresistor\b",r"\bcapacitor\b",r"\binductor\b"]),("phasor_diagram",.94,[r"\bphasors?\b",r"\bphasor diagram\b",r"∠"]),("waveform",.93,[r"\bwaveform\b",r"\bsquare wave\b",r"\bsine wave\b"]),("signal_diagram",.92,[r"\bsignal diagram\b",r"\bsignal[- ]flow\b",r"\bsignal flow\b"]),("block_diagram",.91,[r"\bblock diagram\b"]),("network_diagram",.90,[r"\bnetwork diagram\b",r"\bvertices\b",r"\bedges\b"]),("statistical_plot",.91,[r"\bhistogram\b",r"\bbox plot\b",r"\bscatter plot\b",r"\bstatistical plot\b"]),("venn_diagram",.96,[r"\bvenn diagram\b"]),("probability_diagram",.94,[r"\bprobability tree\b",r"\bprobability diagram\b"]),("number_line",.93,[r"\bnumber line\b"]),("function_plot",.92,[r"\bfunction plot\b",r"\bplot\b.*f\s*\(\s*x\s*\)"]),("coordinate_geometry",.93,[r"\bcoordinate geometry\b",r"\bcoordinate plane\b"]),("geometric_figure",.90,[r"\btriangle\b",r"\bcircle\b",r"\bquadrilateral\b",r"\bgeometric figure\b"]),("vector_diagram",.90,[r"\bvector diagram\b"]),("graph",.75,[r"\bgraph\b",r"\bplot\b"])]
def detect_diagram_type(text):
    low=str(text).lower(); best=None
    for typ,base,pats in RULES:
        hits=tuple(p for p in pats if re.search(p,low,re.I|re.S))
        if hits:
            x=DiagramDetection(typ,min(.99,base+.01*(len(hits)-1)),hits,f"Matched {len(hits)} diagram-family cue(s).")
            if best is None or x.confidence>best.confidence:best=x
    return best
