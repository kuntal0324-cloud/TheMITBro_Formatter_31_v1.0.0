# MILESTONE 26 — ACCEPTANCE

## Reproducible Build + Artifact Integrity Contract

Milestone 26 extends the frozen M25 compiler without breaking the M25 public API.

### Contract

- Public API version remains `1.0`.
- Compiler version remains `25.0` for M25 compatibility.
- Build contract version is `26.0`.
- Input schema version remains `1.0`.
- Structured paper input receives a canonical SHA-256 identity.
- Canonical input hashing is independent of dictionary insertion order.
- Compilation manifests record the input identity and M26 build contract.
- Compilation bundles can be verified without regeneration.
- Verification checks:
  - manifest presence and structure
  - canonical manifest serialization
  - exact artifact set
  - artifact byte counts
  - artifact SHA-256 hashes
  - build contract version
  - input schema version
  - deterministic-build declaration
  - optional expected input identity
- CLI supports offline output-bundle verification.
- M25 regression behavior remains intact.
- Release-cleanliness checks remain enforced.

## Required files

- `src/question_compiler.py`
- `src/public_api.py`
- `src/main.py`
- `tests/test_milestone26_integrity.py`
- `scripts/m26_integrity_audit.py`
- `.github/workflows/m26-integrity.yml`
- `ACCEPTANCE.md`
- `RELEASE_NOTES.md`

## Acceptance commands

```bash
python -m pytest -q tests/test_milestone26_integrity.py
python -m pytest -q tests/test_milestone25_release.py
python scripts/m26_integrity_audit.py
```

### Final acceptance

M26 is accepted only when all three commands pass and the GitHub Actions M26 workflow is green.
