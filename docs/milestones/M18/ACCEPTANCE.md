# Milestone 18 — Engineering Diagram Generation Acceptance

## Purpose

M18 converts the frozen M16 Diagram IR into deterministic, portable SVG engineering diagrams.

M18 owns engineering diagram generation only. Mathematical diagram generation remains M17.

## Engineering families implemented

1. Circuit diagrams
2. Block diagrams
3. Signal-flow diagrams
4. Phasor diagrams
5. Vector diagrams
6. Transformer equivalent circuits
7. Motor diagrams
8. Control-system diagrams
9. Logic circuits
10. Engineering waveforms
11. Network diagrams

## Generation pipeline

```text
Question / structured engineering data
        ↓
M16 Diagram detection / DiagramSpec
        ↓
M18 engineering generator
        ↓
validated engineering IR
        ↓
deterministic SVG renderer
        ↓
SVG output
```

## M18 processors

### Circuit diagrams
Supports canonical component specifications for:
- wires
- resistors
- capacitors
- inductors
- voltage sources
- AC sources
- DC sources
- current sources

### Block diagrams
Supports deterministic block/node and directed-edge layouts.

### Signal-flow diagrams
Supports directed signal edges and labeled signal paths.

### Phasor diagrams
Supports magnitude/angle vectors, including expressions such as `V=10∠30°`.

### Vector diagrams
Supports vector components or polar-derived vectors.

### Transformer equivalent circuits
Generates a standard approximate single-phase equivalent-circuit representation with:
- R1
- X1
- Rc
- Xm
- R2'
- X2'

### Motor diagrams
Generates a structural induction/synchronous motor representation showing:
- stator
- rotor
- rotor bars
- rotational-speed arrow

### Control-system diagrams
Generates the canonical closed-loop structure:
- reference
- summing junction
- plant
- feedback element
- forward and feedback paths

### Logic circuits
Supports:
- AND
- OR
- NOT
- NAND
- NOR
- XOR
- XNOR

### Engineering waveforms
Supports deterministic:
- sine
- square
- triangle
- sawtooth

with amplitude, frequency, phase, and duty-cycle controls where applicable.

### Network diagrams
Supports node/edge topology with deterministic rendering.

## Output boundary

M18 produces standalone SVG.

SVG is intentionally retained as the output boundary because M19 will handle page-level layout and M20/M21 will handle question-paper and PDF/HTML production.

## Conservative behavior

M18 does not claim to be a universal natural-language engineering-diagram solver.

Unsupported or ambiguous engineering requests must fail rather than invent topology.

M18 also rejects mathematical-only requests.

## Regression policy

All previous M15, M16, and M17 tests remain mandatory.

M18 adds its own engineering generation suite.

Current local validation:

```text
137 passed
```

Breakdown:

```text
M15/M16/M17 regression baseline     116 tests
M18 engineering generation          21 tests
----------------------------------------------
Total                               137 tests
```

## SVG validation

The release contains 11 representative engineering SVG samples:

```text
01_circuit_diagram.svg
02_block_diagram.svg
03_signal_diagram.svg
04_phasor_diagram.svg
05_vector_diagram.svg
06_transformer_equivalent.svg
07_motor_diagram.svg
08_control_system.svg
09_logic_circuit.svg
10_waveform.svg
11_network_diagram.svg
```

All samples are checked for:
- valid XML
- no `NaN`
- no `undefined`
- deterministic output

## Acceptance gate

M18 is technically complete only when:

- repository structure passes
- complete regression suite passes
- M17 tests remain green
- all 11 engineering families have generation coverage
- structured engineering DiagramSpec generation works
- representative natural-language canonical requests work
- unsupported mathematical requests are rejected
- invalid structured topology is rejected
- SVG output is valid XML
- deterministic generation is verified
- output-file generation is verified
- GitHub Actions passes the same acceptance suite

## Explicit boundary

M18 does not implement:
- final page layout
- automatic question-paper composition
- PDF pagination
- production HTML packaging
- large-scale regression corpus
- production hardening

Those remain later milestones.

## Next milestone

```text
M18 Engineering Diagram Generation  ← current
        ↓
M19 Layout Engine
        ↓
M20 Question-Paper Renderer
        ↓
M21 PDF / HTML Production
        ↓
M22 Large-scale Regression Testing
        ↓
M23 Production Hardening
```
