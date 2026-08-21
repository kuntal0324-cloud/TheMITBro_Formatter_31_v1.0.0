# MILESTONE 26 — RELEASE NOTES

## Objective

M25 established the public compiler contract and deterministic production artifacts. M26 adds an independent integrity layer so a generated bundle can be identified and verified without rerunning the compiler.

## Added

### Canonical input identity

`src.question_compiler` now provides:

- `canonicalize_paper_input(...)`
- `input_sha256(...)`

The hash uses canonical JSON with sorted keys, UTF-8 encoding, compact separators, and strict JSON numeric serialization.

### Build contract

M26 introduces:

```text
BUILD_CONTRACT_VERSION = "26.0"
INPUT_SCHEMA_VERSION = "1.0"
```

The existing `COMPILER_VERSION = "25.0"` is deliberately preserved so M25 callers are not broken.

### Manifest hardening

Every compilation manifest now records:

- compiler version
- API contract
- M26 build contract
- input schema version
- canonical input SHA-256
- deterministic-build declaration
- question count
- page count
- total marks
- production artifact count
- per-artifact byte count and SHA-256

### Offline bundle verification

`verify_output_bundle(...)` verifies an existing compilation directory without generating or modifying files.

The public API exposes:

```python
get_input_sha256(...)
verify_compilation(...)
```

### CLI

A new verification mode is available:

```bash
python -m src.main --verify-output OUTPUT_DIR
```

Optionally:

```bash
python -m src.main   --verify-output OUTPUT_DIR   --expected-input-sha256 HASH
```

### CI

M26 adds:

```text
.github/workflows/m26-integrity.yml
scripts/m26_integrity_audit.py
tests/test_milestone26_integrity.py
```

The existing `tests.yml` also executes the M26 tests and audit.

## Compatibility

M25 remains frozen:

- API version: `1.0`
- compiler version: `25.0`
- supported formats: `markdown`, `svg`, `pdf`, `html`

M26 is an additive integrity contract, not a replacement for the M25 compiler API.

## Deliberate non-goals

M26 does not:

- change mathematical processing semantics
- add new diagram types
- change the existing rendering layout contract
- silently repair invalid input
- lower any coverage or release gates
- replace M25 regression tests

## Release gate

M26 is complete only when:

1. M26 integrity tests pass.
2. M25 release tests pass.
3. M26 audit passes.
4. Release cleanliness passes.
5. GitHub Actions reports a green M26 workflow.
