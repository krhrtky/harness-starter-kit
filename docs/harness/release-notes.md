Standalone binaries for macOS and Linux, with embedded usage, Skills and JSON schemas.

1. Download the archive matching your OS and CPU, plus its `.sha256` checksum.
2. Verify the checksum and extract the archive.
3. Read `START-HERE.md`, then run `./harnessctl usage agent`.

No external Python is needed by the CLI. Usage and schemas work offline before repository initialization.
Project-specific build/test runtimes are still required for the capabilities you configure.

This release includes ad-hoc signed macOS binaries. Developer ID signing and Apple notarization are not configured.
Windows native is not supported by this release.
