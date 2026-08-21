# Milestone 25 — Public API & End-to-End Question Compilation

M25 freezes the first application-facing contract for TheMITbro Formatter.

## What was added

- `src/public_api.py`
  - public API version `1.0`;
  - stable Markdown formatting function;
  - structured Markdown validation result;
  - end-to-end paper compilation entry point.

- `src/question_compiler.py`
  - deterministic paper compilation;
  - Markdown, SVG, PDF and HTML production;
  - SHA-256 artifact manifest;
  - schema version validation;
  - staging-directory generation;
  - safe replacement of previous output.

- `src/main.py`
  - backward-compatible legacy formatter mode;
  - `--version`;
  - `--compile-json`;
  - `--output-dir`;
  - `--formats`.

- `input/milestone25_e2e_paper.json`
  - representative end-to-end regression paper.

- `tests/test_milestone25_release.py`
  - public API contract tests;
  - deterministic compilation tests;
  - artifact integrity tests;
  - CLI tests;
  - failure/rollback behavior tests.

- `scripts/m25_contract_audit.py`
  - independent M25 structure/API/E2E audit.

- `.github/workflows/m25-contract.yml`
  - M25 CI contract validation and evidence upload.

## Design principle

M25 does not expose internal implementation details as the application contract.
Consumers should import from `src.public_api` rather than coupling themselves
to individual renderer, layout, or solver modules.

## Validation

M25 requires:

- complete regression suite;
- M24 regression;
- M25 contract suite;
- >=90% overall coverage;
- deterministic artifacts;
- manifest hash verification;
- valid SVG/PDF/HTML outputs;
- clean Git-tracked repository.

## Boundary

M25 does not claim universal question solving. It establishes a reliable
compilation boundary around the capabilities already implemented by M15-M24.

See `ACCEPTANCE.md` for the complete acceptance contract.
