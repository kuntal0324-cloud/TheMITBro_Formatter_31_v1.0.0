# Milestone 28 Release Notes

## Added

- 20-paper real-world compatibility corpus.
- 20 distinct mathematical/content families.
- End-to-end corpus compilation tests.
- Determinism checks across representative cases.
- Unicode preservation check.
- Diagram integration check.
- Artifact hash verification.
- Fail-closed malformed-input test.
- Independent M28 corpus audit.
- Dedicated M28 GitHub Actions workflow.

## Compatibility

M28 intentionally keeps the frozen API, input schema, and M26 build contract
unchanged. It adds validation around those contracts rather than silently
versioning or changing them.
