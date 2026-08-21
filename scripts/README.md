


## M25 Contract Audit

`scripts/m25_contract_audit.py` verifies the M25 public API contract and runs
the canonical end-to-end question-paper fixture. It checks the generated
Markdown, SVG, PDF, HTML and SHA-256 manifest.

Run locally:

```bash
PYTHONPATH=. python scripts/m25_contract_audit.py
```

## M27 Quality Audit

`scripts/m27_quality_audit.py` independently exercises the public API against
the M27 representative corpus and verifies deterministic Markdown, SVG, PDF,
HTML and manifest artifacts.

Run locally:

```bash
PYTHONPATH=. python scripts/m27_quality_audit.py
```
