from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2.0, self.y + self.height / 2.0)

    def intersects(self, other: "Rect", padding: float = 0.0) -> bool:
        return not (
            self.right + padding <= other.x
            or other.right + padding <= self.x
            or self.bottom + padding <= other.y
            or other.bottom + padding <= self.y
        )

    def within(self, width: float, height: float, margin: float = 0.0) -> bool:
        return (
            self.x >= margin
            and self.y >= margin
            and self.right <= width - margin
            and self.bottom <= height - margin
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "x": round(self.x, 4),
            "y": round(self.y, 4),
            "width": round(self.width, 4),
            "height": round(self.height, 4),
        }


@dataclass
class LayoutItem:
    id: str
    kind: str
    rect: Rect
    source: Optional[str] = None
    layer: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "rect": self.rect.to_dict(),
            "source": self.source,
            "layer": self.layer,
            "metadata": self.metadata,
        }


@dataclass
class LayoutOptions:
    width: float = 1000.0
    height: float = 650.0
    margin: float = 48.0
    gap: float = 24.0
    title_height: float = 42.0
    min_item_size: float = 18.0
    max_iterations: int = 120
    preserve_explicit_positions: bool = True

    def validate(self) -> "LayoutOptions":
        if self.width <= 2 * self.margin:
            raise ValueError("Layout width is too small for the requested margin.")
        if self.height <= 2 * self.margin + self.title_height:
            raise ValueError("Layout height is too small for the requested margin/title.")
        if self.gap < 0 or self.margin < 0:
            raise ValueError("Layout gap and margin must be non-negative.")
        return self


@dataclass
class LayoutResult:
    diagram_type: str
    width: float
    height: float
    margin: float
    title: Optional[str]
    items: List[LayoutItem] = field(default_factory=list)
    connectors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def content_rect(self) -> Rect:
        return Rect(
            self.margin,
            self.margin + 42.0,
            self.width - 2 * self.margin,
            self.height - 2 * self.margin - 42.0,
        )

    def overlaps(self, padding: float = 0.0) -> List[Tuple[str, str]]:
        pairs: List[Tuple[str, str]] = []
        for i, a in enumerate(self.items):
            for b in self.items[i + 1:]:
                if a.metadata.get("allow_overlap") or b.metadata.get("allow_overlap"):
                    continue
                if a.rect.intersects(b.rect, padding):
                    pairs.append((a.id, b.id))
        return pairs

    def validate(self, padding: float = 0.0) -> List[str]:
        errors: List[str] = []
        if self.width <= 0 or self.height <= 0:
            errors.append("Canvas dimensions must be positive.")
        seen = set()
        for item in self.items:
            if item.id in seen:
                errors.append(f"Duplicate layout item ID: {item.id}")
            seen.add(item.id)
            if item.rect.width <= 0 or item.rect.height <= 0:
                errors.append(f"Non-positive rectangle for {item.id}.")
            if not item.rect.within(self.width, self.height, self.margin):
                errors.append(f"Item outside canvas bounds: {item.id}.")
        for a, b in self.overlaps(padding):
            errors.append(f"Layout overlap: {a} / {b}.")
        return errors

    def ensure_valid(self, padding: float = 0.0) -> "LayoutResult":
        errors = self.validate(padding)
        if errors:
            raise ValueError("; ".join(errors))
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diagram_type": self.diagram_type,
            "width": self.width,
            "height": self.height,
            "margin": self.margin,
            "title": self.title,
            "items": [x.to_dict() for x in self.items],
            "connectors": self.connectors,
            "metadata": self.metadata,
        }
