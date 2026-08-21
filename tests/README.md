# Test suites

The regression suite contains:

- M15 mathematical rendering/processor validation tests
- M16 Diagram IR tests
- M17 mathematical diagram generation tests
- M18 engineering diagram generation tests

Run everything with:

```bash
python -m pytest -q
```

M18-specific tests:

```bash
python -m pytest -q tests/test_milestone18_engineering_generation.py
```


## Milestone 22

`test_milestone22_regression.py` provides the large-scale regression harness. It covers 76 representative cases across all 19 M17/M18 diagram families and validates the M19–M21 production chain.

## Milestone 27

`test_milestone27_quality.py` validates representative end-to-end papers,
deterministic artifacts, Unicode/math content, diagram survival, fail-closed
invalid input handling, and the public API without coupling tests to renderer
implementation details.

Run locally:

```bash
python -m pytest -q tests/test_milestone27_quality.py
```
