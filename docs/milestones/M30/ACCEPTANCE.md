# TheMITbro Formatter — Milestone 30 Acceptance

## Release Candidate / Repository Freeze

M30 converts the M29 development repository into a clean release-candidate repository without changing the frozen M25 public API or M26 build/input contracts.

### Acceptance gates

- [ ] Repository documentation consolidated under `docs/`.
- [ ] Historical milestone records preserved under `docs/milestones/`.
- [ ] No legacy milestone acceptance/release files remain in the repository root.
- [ ] Roadmap, architecture, format specification, and release process documented.
- [ ] M22–M29 regression suite passes.
- [ ] M30 release-candidate tests pass.
- [ ] M30 independent audit passes.
- [ ] Public API remains `1.0`.
- [ ] Build contract remains `26.0`.
- [ ] Input schema remains `1.0`.
- [ ] Representative Markdown/SVG/PDF/HTML production succeeds.
- [ ] Representative artifacts are deterministic.
- [ ] Generated coverage/cache files are not tracked.
- [ ] M30 CI validation passes on GitHub Actions.

## Certification rule

M30 is certified only after the dedicated M30 workflow and the main regression workflow both complete successfully on the repository's default branch.
