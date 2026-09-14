# Harness Starter Kit v1.2.0

Standalone binaries for macOS and Linux (arm64 and x86_64).

## Changes

- Bundle `harness-document`, a dedicated Agent Skill for finding existing authoritative documents, choosing placement, editing within scope, and checking coverage and consistency. The distribution now includes 11 Skills.
- Add `harnessctl usage documentation` to retrieve the complete documentation policy offline, before repository initialization. The policy defines boundaries for all 27 knowledge areas, document formats, coverage checks, and Agent decision procedures.
- Expose the new Skill through `harnessctl usage harness-document`, the Agent guide, and related workflow Skills. Local project rules and explicit user instructions take precedence over bundled common guidance.
- Include a development-process guide explaining Task boundaries, evidence, semantic review, delivery, and repository learning.
- Verify Skill discovery, installation, migration, and protection of locally edited Skills. Native acceptance tests compare every installed Skill with the content returned by the executable.

No schema or existing command contract changes. Documentation coverage and semantic correctness still require review; a passing structural check alone does not establish them.

## Install or upgrade

1. Download the archive matching your OS and CPU, plus its `.sha256` checksum.
2. Verify the checksum, extract the archive, and replace the CLI executable with this version.
3. Read `START-HERE.md`, then run `./harnessctl usage agent`.
4. For an existing initialized repository, run `harnessctl migrate` to inspect updates and conflicts, then `harnessctl migrate --apply` after resolving conflicts. Re-running `init` does not add Skills to an already initialized repository.
5. Read `harnessctl usage harness-document` to use the new documentation workflow. Preserve local documentation rules and merge locally edited Skills rather than overwriting them.

No external Python is needed by the CLI. Usage and schemas work offline before initialization. Project-specific build/test runtimes remain required for configured capabilities.

macOS binaries are ad-hoc signed; Developer ID signing and Apple notarization are not configured. Windows native is not supported.
