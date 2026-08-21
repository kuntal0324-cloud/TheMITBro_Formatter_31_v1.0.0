from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, Iterable, List, Tuple
import math

from .diagram_ir import DiagramSpec
from .layout_ir import LayoutItem, LayoutOptions, LayoutResult, Rect


def _num(value, default=0.0):
    try:
        value = float(value)
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def _size_for_node(node) -> Tuple[float, float]:
    kind = str(node.kind).lower()
    if kind in {"summation", "event", "root"}:
        return (54.0, 54.0)
    if kind in {"vertex"}:
        return (42.0, 42.0)
    w = _num(node.properties.get("width"), 120.0)
    h = _num(node.properties.get("height"), 55.0)
    return (max(36.0, w), max(28.0, h))


def _text_size(text: Any, base=18.0) -> Tuple[float, float]:
    n = max(1, len(str(text or "")))
    return (max(40.0, min(280.0, 10.0 * n + 22.0)), base)


class DiagramLayoutEngine:
    """M19 deterministic layout engine.

    M19 computes geometry only. It does not invent diagram semantics and does
    not replace M16-M18 renderers. The resulting LayoutResult is the stable
    placement contract for M20 question-paper composition.
    """

    def __init__(self, options: LayoutOptions | None = None):
        self.options = (options or LayoutOptions()).validate()

    def layout(self, spec: DiagramSpec, options: LayoutOptions | None = None) -> LayoutResult:
        spec.ensure_valid()
        opts = (options or self.options).validate()
        engine = self if options is None else DiagramLayoutEngine(opts)
        result = engine._layout(spec)
        return result.ensure_valid(padding=0.5)

    def _layout(self, spec: DiagramSpec) -> LayoutResult:
        o = self.options
        result = LayoutResult(
            diagram_type=spec.diagram_type,
            width=o.width,
            height=o.height,
            margin=o.margin,
            title=spec.title,
            metadata={"engine": "M19", "deterministic": True},
        )
        content = result.content_rect
        items = self._extract_items(spec, content)

        if spec.nodes:
            items = self._layout_nodes(spec, items, content)
        elif self._has_geometry_family(spec):
            items = self._fit_geometry(items, content)
        else:
            items = self._pack_items(items, content)

        result.items = items
        result.connectors = self._connectors(spec, items)
        result.metadata["item_count"] = len(items)
        result.metadata["overlap_count"] = len(result.overlaps(0.5))
        result.metadata["content_rect"] = content.to_dict()
        return result

    @staticmethod
    def _has_geometry_family(spec: DiagramSpec) -> bool:
        return bool(
            spec.points
            or spec.series
            or spec.regions
            or spec.expressions
            or spec.properties
        )

    def _extract_items(self, spec: DiagramSpec, content: Rect) -> List[LayoutItem]:
        items: List[LayoutItem] = []

        for node in spec.nodes:
            w, h = _size_for_node(node)
            if node.position is not None:
                x, y = map(_num, node.position)
            else:
                x, y = content.x + w / 2, content.y + h / 2
            items.append(LayoutItem(
                id=f"node:{node.id}",
                kind="node",
                rect=Rect(x - w / 2, y - h / 2, w, h),
                source=node.id,
                metadata={"node_kind": node.kind, "label": node.label or node.id},
            ))

        # Engineering circuit components.
        for i, comp in enumerate(spec.properties.get("components", []) or []):
            x1, y1 = _num(comp.get("x1"), 100), _num(comp.get("y1"), 100)
            x2, y2 = _num(comp.get("x2"), 200), _num(comp.get("y2"), 100)
            w = max(18.0, abs(x2 - x1))
            h = max(18.0, abs(y2 - y1))
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            pad = 16.0
            items.append(LayoutItem(
                id=f"component:{i+1}",
                kind="component",
                rect=Rect(cx - w / 2 - pad, cy - h / 2 - pad, w + 2*pad, h + 2*pad),
                source=str(comp.get("label") or comp.get("type") or i+1),
                metadata={"component_type": comp.get("type"), "label": comp.get("label"), "allow_overlap": True},
            ))

        # Logic gates are represented as centered boxes.
        for i, gate in enumerate(spec.properties.get("gates", []) or []):
            x, y = _num(gate.get("x"), 400), _num(gate.get("y"), 300)
            items.append(LayoutItem(
                id=f"gate:{gate.get('id', i+1)}",
                kind="gate",
                rect=Rect(x - 55, y - 35, 110, 70),
                source=str(gate.get("id", i+1)),
                metadata={"gate_type": gate.get("type", "AND")},
            ))

        # Mathematical points are visual markers, not the entire plot area.
        for i, point in enumerate(spec.points):
            items.append(LayoutItem(
                id=f"point:{point.id or i+1}",
                kind="point",
                rect=Rect(_num(point.x) - 10, _num(point.y) - 10, 20, 20),
                source=point.id,
                metadata={"label": point.label},
            ))

        # Vectors/phasors become line-bounds with padding.
        for i, vec in enumerate(spec.properties.get("vectors", []) or []):
            if "dx" in vec or "dy" in vec:
                x0, y0 = _num(spec.properties.get("origin", (200, 400))[0], 200), _num(spec.properties.get("origin", (200, 400))[1], 400)
                x1, y1 = x0 + _num(vec.get("dx"), 100), y0 + _num(vec.get("dy"), -100)
            else:
                x0, y0 = _num(spec.properties.get("origin", (250, 430))[0], 250), _num(spec.properties.get("origin", (250, 430))[1], 430)
                a = math.radians(_num(vec.get("angle_deg"), 0))
                mag = _num(vec.get("magnitude"), 100)
                x1, y1 = x0 + mag * math.cos(a), y0 - mag * math.sin(a)
            x, y = min(x0, x1), min(y0, y1)
            w, h = max(18, abs(x1-x0)), max(18, abs(y1-y0))
            items.append(LayoutItem(
                id=f"vector:{vec.get('label', i+1)}",
                kind="vector",
                rect=Rect(x-12, y-12, w+24, h+24),
                source=str(vec.get("label", i+1)),
            ))

        # Waveform has a known renderer viewport; represent that viewport.
        if spec.diagram_type == "waveform":
            items.append(LayoutItem(
                id="waveform:plot",
                kind="plot",
                rect=Rect(80, 225, 800, 210),
                source="waveform",
            ))

        if spec.diagram_type == "motor_diagram":
            items.append(LayoutItem(
                id="motor:machine",
                kind="machine",
                rect=Rect(320, 150, 360, 360),
                source="motor",
            ))

        if spec.regions:
            for i, region in enumerate(spec.regions):
                # Venn regions are laid out as equal circles/regions.
                items.append(LayoutItem(
                    id=f"region:{region.id}",
                    kind="region",
                    rect=Rect(300 + i*150, 250, 180, 180),
                    source=region.id,
                    metadata={"label": region.label},
                ))

        if not items:
            tw, th = _text_size(spec.title or spec.diagram_type, 42)
            items.append(LayoutItem(
                id="diagram:content",
                kind="content",
                rect=Rect(content.x, content.y, min(tw, content.width), min(th, content.height)),
            ))

        return items

    def _layout_nodes(self, spec: DiagramSpec, items: List[LayoutItem], content: Rect) -> List[LayoutItem]:
        by_id = {item.source: item for item in items if item.source}
        node_ids = [n.id for n in spec.nodes]
        outgoing = {n: [] for n in node_ids}
        incoming = {n: [] for n in node_ids}
        for edge in spec.edges:
            if edge.source in outgoing and edge.target in incoming:
                outgoing[edge.source].append(edge.target)
                incoming[edge.target].append(edge.source)

        # Stable topological levels. For cycles, remaining nodes are appended
        # in source order to the next deterministic level.
        levels: Dict[str, int] = {}
        queue = [n for n in node_ids if not incoming[n]]
        for n in queue:
            levels[n] = 0
        cursor = 0
        while cursor < len(queue):
            n = queue[cursor]
            cursor += 1
            for target in sorted(outgoing[n], key=node_ids.index):
                proposed = levels[n] + 1
                if proposed > levels.get(target, -1):
                    levels[target] = proposed
                if target not in queue and target not in levels:
                    queue.append(target)

        if len(levels) != len(node_ids):
            next_level = max(levels.values(), default=-1) + 1
            for n in node_ids:
                if n not in levels:
                    levels[n] = next_level
                    next_level += 1

        groups: Dict[int, List[str]] = {}
        for n in node_ids:
            groups.setdefault(levels[n], []).append(n)

        # If a very long chain would make columns too narrow, compress node
        # boxes uniformly but never below the configured minimum.
        level_count = max(groups, default=0) + 1
        widest = max((by_id[n].rect.width for n in node_ids), default=36.0)
        if level_count > 1:
            max_w = (content.width - self.options.gap * (level_count - 1)) / level_count
            if max_w < widest:
                scale = max(self.options.min_item_size, max_w) / widest
                for n in node_ids:
                    item = by_id[n]
                    by_id[n] = replace(
                        item,
                        rect=Rect(
                            item.rect.x,
                            item.rect.y,
                            max(self.options.min_item_size, item.rect.width * scale),
                            max(self.options.min_item_size, item.rect.height * scale),
                        ),
                    )

        col_width = content.width / max(1, level_count)
        out = []
        for level in sorted(groups):
            ids = groups[level]
            count = len(ids)
            for row, node_id in enumerate(ids):
                item = by_id[node_id]
                cx = content.x + col_width * (level + 0.5)
                cy = content.y + content.height * ((row + 1) / (count + 1))
                w, h = item.rect.width, item.rect.height
                by_id[node_id] = replace(
                    item,
                    rect=Rect(cx - w/2, cy - h/2, w, h),
                    layer=level,
                )
            out.extend(by_id[n] for n in ids)

        return self._resolve_overlaps(out, content)

    def _fit_geometry(self, items: List[LayoutItem], content: Rect) -> List[LayoutItem]:
        # Normalize the extracted coordinate-space geometry into the page's
        # content rectangle while preserving relative geometry.
        min_x = min(i.rect.x for i in items)
        min_y = min(i.rect.y for i in items)
        max_x = max(i.rect.right for i in items)
        max_y = max(i.rect.bottom for i in items)
        src_w = max(max_x - min_x, 1.0)
        src_h = max(max_y - min_y, 1.0)
        sx = content.width / src_w
        sy = content.height / src_h
        scale = min(sx, sy, 1.0) if src_w <= content.width and src_h <= content.height else min(sx, sy)
        # Avoid microscopic text/markers after extreme aspect ratios.
        scale = max(0.12, min(scale, 4.0))
        used_w, used_h = src_w*scale, src_h*scale
        ox = content.x + (content.width-used_w)/2 - min_x*scale
        oy = content.y + (content.height-used_h)/2 - min_y*scale
        fitted = [
            replace(
                item,
                rect=Rect(
                    item.rect.x*scale + ox,
                    item.rect.y*scale + oy,
                    max(item.rect.width*scale, self.options.min_item_size),
                    max(item.rect.height*scale, self.options.min_item_size),
                )
            )
            for item in items
        ]
        return self._resolve_overlaps(fitted, content, max_passes=20)

    def _pack_items(self, items: List[LayoutItem], content: Rect) -> List[LayoutItem]:
        if len(items) == 1:
            i = items[0]
            w = min(i.rect.width, content.width)
            h = min(i.rect.height, content.height)
            return [replace(i, rect=Rect(content.x+(content.width-w)/2, content.y+(content.height-h)/2, w, h))]
        cols = max(1, math.ceil(math.sqrt(len(items))))
        rows = math.ceil(len(items)/cols)
        cell_w = content.width / cols
        cell_h = content.height / rows
        out = []
        for idx, item in enumerate(items):
            col, row = idx % cols, idx // cols
            w = min(item.rect.width, cell_w - self.options.gap)
            h = min(item.rect.height, cell_h - self.options.gap)
            x = content.x + col*cell_w + (cell_w-w)/2
            y = content.y + row*cell_h + (cell_h-h)/2
            out.append(replace(item, rect=Rect(x,y,w,h)))
        return self._resolve_overlaps(out, content)

    def _resolve_overlaps(self, items: List[LayoutItem], content: Rect, max_passes: int | None = None) -> List[LayoutItem]:
        out = list(items)
        passes = max_passes if max_passes is not None else self.options.max_iterations
        for _ in range(passes):
            changed = False
            for i in range(len(out)):
                for j in range(i+1, len(out)):
                    a, b = out[i], out[j]
                    if not a.rect.intersects(b.rect, self.options.gap):
                        continue
                    ax, ay = a.rect.center
                    bx, by = b.rect.center
                    dx, dy = bx-ax, by-ay
                    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                        dx = 1.0
                    if abs(dx) >= abs(dy):
                        shift = (a.rect.right + self.options.gap - b.rect.x) if dx >= 0 else (b.rect.right + self.options.gap - a.rect.x)
                        direction = 1 if dx >= 0 else -1
                        a_new = replace(a, rect=Rect(a.rect.x-direction*shift/2,a.rect.y,a.rect.width,a.rect.height))
                        b_new = replace(b, rect=Rect(b.rect.x+direction*shift/2,b.rect.y,b.rect.width,b.rect.height))
                    else:
                        shift = (a.rect.bottom + self.options.gap - b.rect.y) if dy >= 0 else (b.rect.bottom + self.options.gap - a.rect.y)
                        direction = 1 if dy >= 0 else -1
                        a_new = replace(a, rect=Rect(a.rect.x,a.rect.y-direction*shift/2,a.rect.width,a.rect.height))
                        b_new = replace(b, rect=Rect(b.rect.x,b.rect.y+direction*shift/2,b.rect.width,b.rect.height))
                    out[i], out[j] = a_new, b_new
                    changed = True
            # Clamp and then test again.
            out = [replace(i, rect=self._clamp(i.rect, content)) for i in out]
            if not changed or not any(a.rect.intersects(b.rect, self.options.gap) for ix,a in enumerate(out) for b in out[ix+1:]):
                break
        return out

    @staticmethod
    def _clamp(rect: Rect, bounds: Rect) -> Rect:
        w = min(rect.width, bounds.width)
        h = min(rect.height, bounds.height)
        x = min(max(rect.x, bounds.x), bounds.right-w)
        y = min(max(rect.y, bounds.y), bounds.bottom-h)
        return Rect(x,y,w,h)

    def _connectors(self, spec: DiagramSpec, items: List[LayoutItem]) -> List[Dict[str, Any]]:
        lookup = {i.source: i for i in items if i.source}
        connectors = []
        for edge in spec.edges:
            a, b = lookup.get(edge.source), lookup.get(edge.target)
            if not a or not b:
                continue
            ax, ay = a.rect.center
            bx, by = b.rect.center
            connectors.append({
                "source": edge.source,
                "target": edge.target,
                "kind": edge.kind,
                "label": edge.label,
                "directed": edge.directed,
                "start": {"x": round(ax,4), "y": round(ay,4)},
                "end": {"x": round(bx,4), "y": round(by,4)},
            })
        return connectors


def layout_diagram(spec: DiagramSpec, width=1000, height=650, margin=48, gap=24) -> LayoutResult:
    return DiagramLayoutEngine(LayoutOptions(width=width, height=height, margin=margin, gap=gap)).layout(spec)


def layout_question_blocks(blocks: Iterable[Tuple[str, float, float]], width=1000, height=1400, margin=56, gap=28) -> List[LayoutItem]:
    """Lay out question-paper blocks top-to-bottom.

    Each tuple is (block_id, requested_width, requested_height). Blocks are
    clamped to the page content width and packed deterministically.
    """
    content = Rect(margin, margin, width-2*margin, height-2*margin)
    y = content.y
    result: List[LayoutItem] = []
    for block_id, req_w, req_h in blocks:
        w = min(max(1.0, float(req_w)), content.width)
        h = min(max(1.0, float(req_h)), content.bottom-y)
        if h <= 0:
            raise ValueError("Question blocks exceed available page height.")
        result.append(LayoutItem(block_id, "question_block", Rect(content.x, y, w, h)))
        y += h + gap
    return result
