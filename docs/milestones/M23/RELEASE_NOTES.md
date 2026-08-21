# Milestone 23 Release Notes

## Added

- `tests/test_milestone23_hardening.py`
- CLI success/failure regression tests
- mathematical normalization edge-case tests
- explicit 90% overall coverage gate
- critical production-module coverage gate
- Python source compilation validation
- M23 CI evidence artifacts

## Improved

- upgraded the minimum supported `pytest-cov` version to 7.1.0 for the M23 coverage gate
- upgraded GitHub Actions artifact upload to `actions/upload-artifact@v6` for Node 24 runtime compatibility

## Preserved

All M15–M22 mathematical, diagram, layout, rendering, production, and regression behavior remains under the complete regression suite.

## Boundary

M23 is production hardening. It does not add new diagram families or replace the M22 regression corpus.
