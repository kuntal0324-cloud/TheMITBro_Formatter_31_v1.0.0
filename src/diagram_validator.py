from dataclasses import dataclass
from .diagram_ir import DiagramSpec
@dataclass
class DiagramValidation:
    valid:bool; errors:list[str]
def validate_diagram(spec:DiagramSpec):
    e=spec.validate(); return DiagramValidation(not e,e)
