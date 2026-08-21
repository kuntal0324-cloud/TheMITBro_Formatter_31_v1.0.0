# Milestone 16 — Diagram Representation Acceptance

## Purpose
M16 creates the unified Diagram Intermediate Representation (IR). It is the structural layer consumed by M17/M18 generators.

### Mathematical families
- coordinate geometry
- graphs
- geometric figures
- probability diagrams
- Venn diagrams
- function plots
- number lines
- statistical plots

### Engineering families
- circuit diagrams
- block diagrams
- signal diagrams
- phasor diagrams
- vector diagrams
- transformer equivalent circuits
- motor diagrams
- control-system diagrams
- logic circuits
- waveforms
- network diagrams

### M16 provides
- typed points, labels, axes, nodes, edges, series and regions
- expressions, annotations, properties and metadata
- JSON serialization/deserialization
- structural validation
- conservative family detection
- deterministic construction from structured data

### Explicit boundary
M16 does **not** render SVG/PNG/PDF and does not claim universal natural-language diagram understanding. Generation begins in M17/M18.

### Acceptance gate
M15 regression suite green + M16 diagram-IR suite green + all agreed families registered + invalid specifications rejected + JSON round-trip preserved + GitHub CI green.
