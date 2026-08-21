from src.diagram_detector import detect_diagram_type
from src.diagram_engine import DiagramEngine
from src.diagram_ir import *
from src.diagram_parser import build_diagram_spec,make_graph,make_function_plot,make_venn,make_network
from src.diagram_validator import validate_diagram
def test_registry():
 assert len(DIAGRAM_TYPES)==19
def test_math_families():
 assert coordinate_spec([(1,2)]).category()=="mathematical"; assert make_graph(["y=x^2"]).diagram_type=="graph"; assert make_function_plot("y=sin(x)").diagram_type=="function_plot"
def test_geometric_probability_venn_numberline_stats():
 assert validate_diagram(DiagramSpec("geometric_figure",points=[Point(0,0),Point(1,0)])).valid
 assert validate_diagram(DiagramSpec("probability_diagram",nodes=[Node("S","event"),Node("H","outcome")],edges=[Edge("S","H")])).valid
 assert make_venn([Region("A","set")]).diagram_type=="venn_diagram"
 assert validate_diagram(DiagramSpec("number_line",points=[Point(0,0)])).valid
 assert validate_diagram(DiagramSpec("statistical_plot",series=[Series(values=[1,2,3])])).valid
def test_engineering_families():
 for t in ENGINEERING_TYPES:
  assert DiagramSpec(t).category()=="engineering"
def test_network_and_topology():
 s=make_network([Node("A","vertex"),Node("B","vertex")],[Edge("A","B")]); assert validate_diagram(s).valid
 assert not validate_diagram(DiagramSpec("network_diagram",nodes=[Node("A","vertex")],edges=[Edge("A","B")])).valid
def test_special_engineering_properties():
 for t in ["transformer_equivalent_circuit","motor_diagram","control_system_diagram","logic_circuit","waveform"]: assert validate_diagram(DiagramSpec(t,properties={"model":"M16"})).valid
def test_roundtrip():
 s=coordinate_spec([(1,2)],title="AB"); assert DiagramSpec.from_json(s.to_json()).to_dict()==s.to_dict()
def test_structured_parser():
 s=build_diagram_spec({"diagram_type":"coordinate_geometry","coordinate_system":"cartesian","axes":[{"name":"x"},{"name":"y"}],"points":[{"x":1,"y":2,"id":"A"}]}); assert s.points[0].id=="A"
def test_detectors_math():
 assert detect_diagram_type("Draw the coordinate plane with points A and B.").diagram_type=="coordinate_geometry"
 assert detect_diagram_type("Draw a Venn diagram.").diagram_type=="venn_diagram"
 assert detect_diagram_type("Draw a probability tree.").diagram_type=="probability_diagram"
 assert detect_diagram_type("Plot f(x) as a function plot.").diagram_type=="function_plot"
def test_detectors_engineering():
 assert detect_diagram_type("Draw the transformer equivalent circuit with R1 and X1.").diagram_type=="transformer_equivalent_circuit"
 assert detect_diagram_type("Draw the induction motor showing stator and rotor.").diagram_type=="motor_diagram"
 assert detect_diagram_type("Draw the closed-loop control system with feedback.").diagram_type=="control_system_diagram"
 assert detect_diagram_type("Draw the NAND logic circuit.").diagram_type=="logic_circuit"
 assert detect_diagram_type("Plot the square wave waveform.").diagram_type=="waveform"
def test_detector_statistical_and_conservative():
 assert detect_diagram_type("Plot a histogram.").diagram_type=="statistical_plot"
 assert detect_diagram_type("Solve x^2-5x+6=0.") is None
def test_pipeline():
 r=DiagramEngine().process("Draw the coordinate plane.",{"diagram_type":"coordinate_geometry","coordinate_system":"cartesian","axes":[{"name":"x"},{"name":"y"}],"points":[{"x":0,"y":0,"id":"O"}]}); assert r["detection"]["diagram_type"]=="coordinate_geometry" and r["spec"]["points"][0]["id"]=="O"
def test_invalid_and_constraints():
 assert not validate_diagram(DiagramSpec("invalid_type")).valid
 assert not validate_diagram(DiagramSpec("venn_diagram")).valid
 assert not validate_diagram(DiagramSpec("coordinate_geometry",points=[Point(1,2)])).valid
