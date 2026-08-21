# TheMITbro Formatter — Milestone 27 Acceptance

## Production-Quality End-to-End Validation

Milestone 27 adds a product-level quality contract on top of the M25 release
contract and M26 reproducible-build/artifact-integrity contract.

### M27 goals

- Validate the public API through realistic end-to-end papers.
- Exercise mathematical Markdown, options, Unicode, metadata, and diagrams.
- Compile every production format supported by the frozen compiler contract.
- Verify generated artifacts without regenerating them.
- Prove deterministic output for repeated compilation.
- Prove fail-closed behavior for invalid input and invalid output targets.
- Detect malformed production artifacts such as invalid SVG, PDF, HTML, or
  Markdown output.
- Keep the existing M22–M26 regression contracts intact.
- Keep generated test/build files out of the repository.

### M27 acceptance gates

- [ ] M27 quality tests pass.
- [ ] M27 quality audit passes.
- [ ] Existing M22 regression passes.
- [ ] Existing M23 hardening passes.
- [ ] Existing M24 release tests pass.
- [ ] Existing M25 release tests and contract audit pass.
- [ ] Existing M26 integrity tests and audit pass.
- [ ] Overall coverage remains at least 90%.
- [ ] Critical production modules remain at least 90%.
- [ ] Release cleanliness passes.
- [ ] GitHub Actions M27 workflow is green.

### Contract boundary

M27 does **not** silently change the frozen M25 public API or M26 build
contract. It adds validation around those contracts. A future milestone may
version a new production contract explicitly.

**Status: IN PROGRESS**
