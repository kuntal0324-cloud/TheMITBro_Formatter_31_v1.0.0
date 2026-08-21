# Release Process

## Development milestones

Each milestone must have automated tests and an independent audit where applicable.

## Release Candidate (M30)

M30 must pass:

1. complete regression;
2. M22–M29 milestone checks;
3. documentation/repository structure audit;
4. public API/build-contract audit;
5. representative production compilation;
6. deterministic artifact verification;
7. release cleanliness checks.

## Final Release (M31)

M31 repeats the complete release-candidate validation and freezes the Formatter 1.0 contract.

Generated files such as `.coverage`, `coverage/`, `.pytest_cache/`, and Python bytecode must never be committed.
