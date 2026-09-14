# v1.2.0 release

Task: `.harness/tasks/release-1-2-0.json`。Owner: harness-maintainers。

## Scope and placement

Publish the documentation policy, CLI discovery routes, and harness-document through the existing four-platform tag workflow. Version metadata stays in pyproject.toml and the package version module; release notes stay in the existing release-notes.md. Update the installation example to the same version. Do not change repository visibility, schemas, policies, or capabilities.

## Evidence and delivery

Run test.unit, verify.formal, and verify.properties after the version update. Review the release diff and require the existing tagged workflow to pass contract checks, native build, binary-only smoke, and packaging for all four targets. Confirm the release has four archives and their checksums before final delivery review.

The commit includes the documentation and Skill changes already present in this workstream, including their process guide and references. Exclude .DS_Store and local generated build/cache/output files. Preserve the prior release tags.

## Publication

Commit the reviewed release contents and push main and the new v1.2.0 tag through the configured origin. GitHub Actions publishes only after all matrix builds pass. Read the resulting release and verify its assets against the expected macOS/Linux arm64/x86_64 targets. If a build fails, inspect its cause before publishing or changing any tag; do not replace an existing release silently.
