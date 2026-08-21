from __future__ import annotations

from .layout_ir import LayoutResult


def validate_layout(result: LayoutResult, padding: float = 0.5) -> bool:
    result.ensure_valid(padding=padding)
    return True


def layout_report(result: LayoutResult) -> dict:
    errors = result.validate(padding=0.5)
    return {
        "valid": not errors,
        "errors": errors,
        "items": len(result.items),
        "connectors": len(result.connectors),
        "overlaps": len(result.overlaps(0.5)),
        "bounds": {"width": result.width, "height": result.height, "margin": result.margin},
    }
