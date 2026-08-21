# TheMITbro Formatter — Milestone 24
## Release Certification & Reproducible Release Engineering

Milestone 24 follows Milestone 23 Production Hardening.

### Objective

Turn a green CI build into a **release-candidate certification**.

M23 proves that the production pipeline is healthy:
- regression suite passes,
- M22 regression passes,
- M23 hardening tests pass,
- overall coverage is at least 90%,
- critical production modules are at least 90%,
- M17/M18 SVG corpus is valid,
- M19 layout corpus is valid,
- M20/M21 production artifacts are valid,
- generated cache/coverage files are not tracked.

M24 adds the release-engineering layer around that validated code.

### M24 deliverables

1. Release audit
   - no tracked Python cache/bytecode;
   - no tracked coverage output;
   - no tracked pytest cache;
   - no tracked `.env` files;
   - no obvious private-key material;
   - required release metadata exists.

2. Reproducible source manifest
   - deterministic file ordering;
   - SHA-256 for every tracked release file;
   - generated artifacts excluded from the manifest;
   - manifest contains the exact source commit when running in CI.

3. Release bundle
   - source bundle generated from Git-tracked files;
   - SHA-256 checksum generated;
   - bundle is uploaded as a CI artifact;
   - no `.git/`, cache, coverage, or local environment data is included.

4. Release-candidate CI
   - Python source compilation;
   - M23 regression/hardening suites;
   - release audit;
   - deterministic manifest check;
   - release bundle creation;
   - checksum verification;
   - release evidence upload.

5. Pull-request dependency review
   - dependency changes are checked before merge;
   - workflow uses read-only repository permissions.

6. Release policy
   - no release is considered certified merely because a tag exists;
   - certification requires the M24 release workflow to pass;
   - the exact commit SHA and checksum are retained as release evidence.

### Explicit non-goals

M24 does not:
- redesign the formatter;
- add new mathematical domains;
- replace M22 regression data;
- lower the 90% coverage gate;
- silently ignore missing production modules;
- commit generated coverage reports to Git;
- claim universal mathematical correctness.

### Acceptance gates

M24 is complete only when all are true:

- M23 remains green.
- M24 release audit passes.
- Release manifest generation is deterministic.
- Source bundle contains only intended tracked files.
- SHA-256 checksum verifies successfully.
- Dependency-review workflow is valid.
- Release candidate artifact is uploaded successfully.
- Release documentation identifies the certified commit.

### Release flow

```text
Developer commit
      |
      v
M23 Production Hardening
      |
      v
M24 Release Audit
      |
      v
Deterministic Source Manifest
      |
      v
Source Release Bundle
      |
      v
SHA-256 Verification
      |
      v
Release Candidate Artifact
      |
      v
Certified Release
```

### Recommended next milestone

M25 should focus on **public API / CLI contract stabilization and end-to-end question compilation**, not another generic increase in test count.
