# TheMITbro Formatter — Milestone 25
## Public API Stabilization & End-to-End Question Compilation

Milestone 25 follows M24 Release Certification.

### Objective

Freeze a small, application-facing contract around the existing formatter and
production pipeline so that TheMITbro website, Question Bank, and future tools
can call the formatter without depending on internal implementation modules.

M25 also introduces a deterministic end-to-end compiler for a structured
question-paper document.

### M25 deliverables

1. **Public API contract**
   - `src.public_api.API_VERSION == "1.0"`
   - `format_markdown(text)`
   - `validate_markdown(text)`
   - `compile_paper(paper, output_dir, formats=...)`
   - structured validation and compilation results
   - unsupported input types fail explicitly

2. **End-to-end compiler**
   - accepts the existing `PaperSpec` dictionary contract;
   - accepts optional `schema_version`, currently `1.0`;
   - rejects unsupported schema versions;
   - validates the paper before production;
   - produces requested Markdown/SVG/PDF/HTML outputs;
   - always produces a machine-readable `manifest.json`;
   - records SHA-256 and byte size for every generated artifact.

3. **Atomic production behavior**
   - generation happens in a temporary staging directory;
   - an existing output directory is replaced only after successful generation;
   - failed validation does not destroy a previous successful output;
   - stale files are removed on a successful replacement.

4. **Public CLI contract**
   - existing Markdown formatter invocation remains supported;
   - `--version` reports the public API contract;
   - `--compile-json` enables end-to-end paper compilation;
   - `--output-dir` controls the compilation destination;
   - `--formats` selects `markdown`, `svg`, `pdf`, and/or `html`.

5. **M25 regression fixture**
   - representative GATE/engineering-mathematics paper;
   - mathematical notation;
   - MCQ options;
   - mathematical diagram;
   - engineering diagram;
   - production output validation.

6. **M25 CI**
   - source compilation;
   - complete regression suite;
   - M24 regression;
   - M25 contract tests;
   - overall coverage gate remains at 90%;
   - public CLI validation;
   - M25 contract audit;
   - generated-file cleanliness;
   - CI evidence uploaded as an artifact.

### Explicit non-goals

M25 does not:

- replace the M20 renderer;
- replace M21 PDF/HTML production;
- redesign the mathematical solver;
- add new mathematical domains;
- claim that natural-language questions are universally solvable;
- silently repair invalid PaperSpec data;
- lower the existing 90% coverage requirement;
- commit generated production artifacts or coverage reports.

### Contract

```text
                    TheMITbro Formatter
                           |
                +----------+----------+
                |                     |
          format_markdown()     validate_markdown()
                |                     |
                +----------+----------+
                           |
                    compile_paper()
                           |
             +-------------+-------------+
             |             |             |
          Markdown        SVG       PDF / HTML
             |             |             |
             +-------------+-------------+
                           |
                    manifest.json
                           |
                        SHA-256
```

### Input contract

The compiler accepts the same structured question-paper fields already used by
`PaperSpec.from_dict`:

- `title`
- `questions`
- `subject`
- `exam`
- `duration_minutes`
- `total_marks`
- `instructions`
- `metadata`

M25 additionally recognizes:

```json
{
  "schema_version": "1.0"
}
```

Unknown schema versions are rejected rather than guessed.

### Output contract

A successful compilation returns:

```text
status
compiler_version
api_contract
question_count
page_count
total_marks
output_dir
artifacts[]
```

Each artifact records:

```text
kind
path
sha256
bytes
```

### Acceptance gates

M25 is complete only when all are true:

- M23 remains green.
- M24 remains green.
- M25 tests pass.
- Public API contract tests pass.
- Legacy CLI formatting remains functional.
- End-to-end paper compilation succeeds.
- SVG output is valid and contains no `NaN`/`undefined`.
- PDF has a valid PDF header and EOF marker.
- HTML is self-contained and contains the generated SVG.
- Manifest hashes match the generated artifacts.
- Deterministic repeated compilation produces identical artifacts.
- Existing successful output survives a failed replacement attempt.
- Overall coverage remains at least 90%.
- M25 contract audit passes.
- Generated cache/report files are not tracked.

### Release boundary

M25 is a **contract milestone**, not a feature-expansion milestone.

The internal solver, diagram generators, layout engine, renderer and production
modules remain the implementation layers behind the public API.

The next milestone should therefore focus on **large-scale question-batch QA,
input normalization robustness, and corpus-driven failure classification**.

### Recommended sequence

```text
M23  Production Hardening             ✅
 ↓
M24  Release Certification            ✅
 ↓
M25  Public API + E2E Compilation     ← THIS MILESTONE
 ↓
M26  Large-Scale Question QA
 ↓
M27  Mathematical Fidelity
 ↓
M28  Diagram / Rendering Fidelity
 ↓
M29  Performance & Scalability
 ↓
M30  Final Release Candidate
 ↓
Formatter v1.0
```
