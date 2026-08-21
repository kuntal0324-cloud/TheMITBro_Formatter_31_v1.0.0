from .diagram_ir import *
def _points(values):
    out=[]
    for v in values:
        if isinstance(v,Point):out.append(v)
        elif isinstance(v,dict):out.append(Point(**v))
        else:out.append(Point(float(v[0]),float(v[1])))
    return out
def build_diagram_spec(data):
    d=dict(data); d["points"]=_points(d.get("points",[])); d["labels"]=[x if isinstance(x,Label) else Label(**x) for x in d.get("labels",[])]; d["axes"]=[x if isinstance(x,Axis) else Axis(**x) for x in d.get("axes",[])]; d["nodes"]=[x if isinstance(x,Node) else Node(**x) for x in d.get("nodes",[])]; d["edges"]=[x if isinstance(x,Edge) else Edge(**x) for x in d.get("edges",[])]; d["series"]=[x if isinstance(x,Series) else Series(**{**x,"points":_points(x.get("points",[]))}) for x in d.get("series",[])]; d["regions"]=[x if isinstance(x,Region) else Region(**x) for x in d.get("regions",[])]; return DiagramSpec(**d).ensure_valid()
def make_graph(expressions,title=None):return DiagramSpec("graph",title=title,coordinate_system="cartesian",expressions=list(expressions),axes=[Axis("x",label="x",grid=True),Axis("y",label="y",grid=True)]).ensure_valid()
def make_function_plot(expression,title=None):return DiagramSpec("function_plot",title=title,coordinate_system="cartesian",expressions=[expression],axes=[Axis("x",label="x",grid=True),Axis("y",label="y",grid=True)]).ensure_valid()
def make_venn(regions,title=None):return DiagramSpec("venn_diagram",title=title,regions=regions).ensure_valid()
def make_network(nodes,edges,title=None):return DiagramSpec("network_diagram",title=title,nodes=nodes,edges=edges).ensure_valid()
