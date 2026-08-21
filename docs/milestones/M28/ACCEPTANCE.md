# TheMITbro Formatter — Milestone 28 Acceptance

## Real-World Corpus / Compatibility Validation

M28 converts the M27 end-to-end quality contract into a broader representative
corpus contract. The goal is not to inflate test counts; it is to measure how
much realistic mathematical content can pass through the formatter without
manual repair.

### M28 contract

- 20 representative papers.
- 20 distinct content families.
- At least 3 questions per paper.
- All four production formats tested per corpus paper.
- Deterministic repeated compilation tested.
- Manifest and artifact hashes verified.
- Unicode mathematics tested.
- Diagram integration tested.
- Malformed input must fail closed.
- Existing M22-M27 contracts remain intact.
- Overall and critical production coverage remain >= 90%.
- Release cleanliness remains mandatory.

### Completion gates

- [ ] M28 corpus tests pass.
- [ ] M28 independent audit passes.
- [ ] Complete regression passes.
- [ ] M22-M27 regression contracts pass.
- [ ] Overall coverage >= 90%.
- [ ] Critical production coverage >= 90%.
- [ ] Release cleanliness passes.
- [ ] GitHub Actions M28 workflow is green.

**Status: IN PROGRESS**
