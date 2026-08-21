from .diagram_detector import detect_diagram_type
from .diagram_parser import build_diagram_spec
from .diagram_validator import validate_diagram
class DiagramEngine:
    def detect(self,question):return detect_diagram_type(question)
    def build(self,data):return build_diagram_spec(data)
    def validate(self,spec):return validate_diagram(spec)
    def process(self,question,data=None):
        d=self.detect(question); s=self.build(data) if data is not None else None
        return {"detection":None if d is None else {"diagram_type":d.diagram_type,"confidence":d.confidence,"matched_terms":list(d.matched_terms),"reason":d.reason},"spec":None if s is None else s.to_dict()}
_default=DiagramEngine(); detect=_default.detect; build=_default.build; validate=_default.validate
