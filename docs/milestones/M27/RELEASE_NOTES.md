# Milestone 27 Release Notes

## Production-Quality End-to-End Validation

### Added

- `tests/test_milestone27_quality.py`
- `scripts/m27_quality_audit.py`
- `input/milestone27_quality_corpus.json`
- `.github/workflows/m27-quality.yml`
- M27 acceptance and release documentation

### Validation improvements

M27 validates the formatter as a product pipeline rather than only validating
individual implementation functions:

```text
structured input
      ↓
public API
      ↓
question compiler
      ↓
Markdown / SVG / PDF / HTML
      ↓
manifest
      ↓
artifact verification
      ↓
quality assertions
```

### Design rule

M27 intentionally preserves the M25 API contract and M26 build contract.
The milestone adds quality gates instead of changing existing behavior merely
to make tests pass.

**Release status: IN PROGRESS**
