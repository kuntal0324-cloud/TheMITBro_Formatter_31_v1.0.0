from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import json

DIAGRAM_TYPES=("coordinate_geometry","graph","geometric_figure","probability_diagram","venn_diagram","function_plot","number_line","statistical_plot","circuit_diagram","block_diagram","signal_diagram","phasor_diagram","vector_diagram","transformer_equivalent_circuit","motor_diagram","control_system_diagram","logic_circuit","waveform","network_diagram")
MATHEMATICAL_TYPES={"coordinate_geometry","graph","geometric_figure","probability_diagram","venn_diagram","function_plot","number_line","statistical_plot"}
ENGINEERING_TYPES=set(DIAGRAM_TYPES)-MATHEMATICAL_TYPES
class DiagramValidationError(ValueError): pass
@dataclass
class Point: x:float; y:float; id:Optional[str]=None; label:Optional[str]=None
@dataclass
class Label: text:str; target:Optional[str]=None; position:Optional[Tuple[float,float]]=None
@dataclass
class Node: id:str; kind:str; label:Optional[str]=None; position:Optional[Tuple[float,float]]=None; properties:Dict[str,Any]=field(default_factory=dict)
@dataclass
class Edge: source:str; target:str; kind:str="line"; label:Optional[str]=None; directed:bool=False; properties:Dict[str,Any]=field(default_factory=dict)
@dataclass
class Axis: name:str; minimum:Optional[float]=None; maximum:Optional[float]=None; label:Optional[str]=None; grid:bool=False
@dataclass
class Series: name:Optional[str]=None; points:List[Point]=field(default_factory=list); values:List[float]=field(default_factory=list); kind:str="line"; properties:Dict[str,Any]=field(default_factory=dict)
@dataclass
class Region: id:str; kind:str; label:Optional[str]=None; members:List[str]=field(default_factory=list); properties:Dict[str,Any]=field(default_factory=dict)
@dataclass
class DiagramSpec:
    diagram_type:str
    title:Optional[str]=None
    coordinate_system:Optional[str]=None
    points:List[Point]=field(default_factory=list)
    labels:List[Label]=field(default_factory=list)
    axes:List[Axis]=field(default_factory=list)
    nodes:List[Node]=field(default_factory=list)
    edges:List[Edge]=field(default_factory=list)
    series:List[Series]=field(default_factory=list)
    regions:List[Region]=field(default_factory=list)
    expressions:List[str]=field(default_factory=list)
    annotations:List[str]=field(default_factory=list)
    properties:Dict[str,Any]=field(default_factory=dict)
    metadata:Dict[str,Any]=field(default_factory=dict)
    def category(self):
        if self.diagram_type in MATHEMATICAL_TYPES:return "mathematical"
        if self.diagram_type in ENGINEERING_TYPES:return "engineering"
        raise DiagramValidationError(f"Unsupported diagram type: {self.diagram_type}")
    def validate(self):
        e=[]
        if self.diagram_type not in DIAGRAM_TYPES:e.append(f"Unsupported diagram type: {self.diagram_type}")
        ids=[n.id for n in self.nodes]
        if len(ids)!=len(set(ids)):e.append("Node IDs must be unique.")
        known=set(ids)
        for edge in self.edges:
            if edge.source not in known:e.append(f"Edge source not found: {edge.source}")
            if edge.target not in known:e.append(f"Edge target not found: {edge.target}")
        for p in self.points:
            if not isinstance(p.x,(int,float)) or not isinstance(p.y,(int,float)):e.append("Point coordinates must be numeric.")
        if self.diagram_type in {"coordinate_geometry","graph","function_plot"} and not self.axes and not self.coordinate_system:e.append(f"{self.diagram_type} requires axes or coordinate_system.")
        if self.diagram_type=="venn_diagram" and not self.regions:e.append("Venn diagrams require regions.")
        return e
    def ensure_valid(self):
        e=self.validate()
        if e:raise DiagramValidationError("; ".join(e))
        return self
    def to_dict(self):return asdict(self)
    def to_json(self,indent=2):return json.dumps(self.to_dict(),indent=indent,ensure_ascii=False)
    @classmethod
    def from_dict(cls,d):
        d=dict(d); d["points"]=[Point(**x) for x in d.get("points",[])]; d["labels"]=[Label(**x) for x in d.get("labels",[])]; d["axes"]=[Axis(**x) for x in d.get("axes",[])]; d["nodes"]=[Node(**x) for x in d.get("nodes",[])]; d["edges"]=[Edge(**x) for x in d.get("edges",[])]; d["series"]=[Series(**{**x,"points":[Point(**p) for p in x.get("points",[])]}) for x in d.get("series",[])]; d["regions"]=[Region(**x) for x in d.get("regions",[])]; return cls(**d)
    @classmethod
    def from_json(cls,text):return cls.from_dict(json.loads(text)).ensure_valid()
def coordinate_spec(points,title=None):
    return DiagramSpec("coordinate_geometry",title=title,coordinate_system="cartesian",points=[p if isinstance(p,Point) else Point(*p) for p in points],axes=[Axis("x",label="x",grid=True),Axis("y",label="y",grid=True)]).ensure_valid()
