# TheMITbro Formatter — Milestone 20 Acceptance

## Milestone

**Milestone 20 — Question-Paper Renderer**

## Objective

Compose the existing M15-M19 capabilities into a deterministic question-paper
rendering layer. M20 consumes formatted question text, validated DiagramSpec
objects, and the M19 placement contract. It does not perform PDF/HTML packaging.

## Required capabilities

- [x] Structured question-paper IR
- [x] Question numbering and marks
- [x] Paper title, subject, exam, duration and instructions
- [x] Deterministic page geometry
- [x] Top-to-bottom question composition using M19 layout blocks
- [x] Automatic pagination without splitting a question block
- [x] Inline mathematical text preservation through M15 formatter
- [x] Multiple-choice option rendering
- [x] M17 mathematical diagram embedding
- [x] M18 engineering diagram embedding
- [x] Machine-readable page/item manifest
- [x] Page and item bounds validation
- [x] Deterministic SVG page output
- [x] Input PaperSpec remains unchanged
- [x] Full regression suite retained

## Boundary

M20 is the composition/rendering layer. It does **not** produce final PDF files,
HTML packages, browser assets, or publication bundles. Those belong to M21.

M20 also does not solve questions or invent diagrams. Questions and diagrams are
inputs from the earlier processing layers.

## Acceptance gate

The following must pass in CI:

1. complete regression suite
2. dedicated M20 tests
3. deterministic output checks
4. page bounds validation
5. SVG XML validation
6. representative mathematical and engineering diagram embedding
7. M20 acceptance summary

A green CI run is required before M21 begins.
