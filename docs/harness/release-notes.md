# Harness Starter Kit v1.2.1

Standalone binaries for macOS and Linux (arm64 and x86_64).

## Changes

- Clarify when a document should be an ADR: classify by its primary purpose, while preserving explicit user instructions and existing authoritative documents. Including a rationale or alternatives does not turn an entire specification or design document into an ADR.
- Distinguish document format from decision status. Unresolved proposals remain unresolved; explicitly requested draft ADRs retain their format and draft status.
- Update `harness-document` to apply the ADR boundary guidance, with a fallback for repositories using older local documentation rules.

No schema or existing command contract changes.

## Install or upgrade

1. Download the archive matching your OS and CPU, plus its `.sha256` checksum.
2. Verify the checksum, extract the archive, and replace the CLI executable with this version.
3. Read `START-HERE.md`, then run `./harnessctl usage agent`.
4. For an existing initialized repository, run `harnessctl migrate` to inspect updates and conflicts, then `harnessctl migrate --apply` after resolving conflicts. Re-running `init` does not add Skills to an already initialized repository.
5. Read `harnessctl usage harness-document` to read the updated documentation workflow. Preserve local documentation rules and merge locally edited Skills rather than overwriting them.

No external Python is needed by the CLI. Usage and schemas work offline before initialization. Project-specific build/test runtimes remain required for configured capabilities.

macOS binaries are ad-hoc signed; Developer ID signing and Apple notarization are not configured. Windows native is not supported.
