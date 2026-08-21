# TheMITbro Formatter — M29 Release Notes

## Summary

M29 moves the formatter from broad real-world compatibility testing into targeted completeness work.

## Changes

### Mathematical normalization

- Added superscript `¹` normalization.
- Added `±`, `∓`, `×`, `÷`, `−`, `→`, `⇒`, and `⇔` normalization.
- Existing Unicode mathematical normalization remains intact.
- Existing `\\operatorname` and `\\dfrac` normalization remains intact.

### Markdown formatting

Mathematical Unicode and legacy operator commands embedded in prose are normalized without forcing the surrounding prose into a math block.

### Validation

M29 adds explicit tests for:

- unbalanced braces
- unbalanced `\\left` / `\\right`
- unbalanced display-math delimiters
- mixed Unicode/operator normalization
- line-ending stability
- empty question text
- duplicate question IDs
- unsupported output formats
- option preservation
- fail-closed malformed structured input

### CI

Added:

```text
.github/workflows/m29-completeness.yml
scripts/m29_completeness_audit.py
tests/test_milestone29_completeness.py
```

## Compatibility

M29 preserves the existing public API and the M22–M28 regression contracts.

## Certification

M29 becomes certified only after its GitHub Actions workflow reports:

```text
MILESTONE 29 CI VALIDATION PASSED
```
