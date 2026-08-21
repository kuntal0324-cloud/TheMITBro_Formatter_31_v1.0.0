
## Milestone 24 — Release Certification

Milestone 24 adds release engineering around the hardened production pipeline.

It produces:
- a tracked-source release bundle;
- deterministic SHA-256 file manifests;
- a bundle checksum;
- a release audit;
- a certification record;
- dependency review for pull requests.

Release artifacts are generated in CI and are not committed to the repository.

See `ACCEPTANCE.md`.
