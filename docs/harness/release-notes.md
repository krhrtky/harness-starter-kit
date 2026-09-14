# Harness Starter Kit v1.1.0

Standalone binaries for macOS and Linux (arm64 and x86_64).

## Changes

- Add `harnessctl result validate --schema <path> --input <path>` to evaluate tool-produced JSON against a repository-owned JSON Schema 2020-12 contract. Exit codes distinguish acceptance (0), contract mismatch (1), and invalid inputs/schema (2).
- Validate results offline, reject duplicate JSON members and non-JSON constants, and bind schemas to the source snapshot. Result validation does not replace producer exit checks or evidence freshness checks.
- Include verification delegation guidance and `usage verification` / `usage verification-tools` in the executable and initialized repositories.
- Add optional pinned Quint 0.32.0 + Apalache 0.56.1 and Hypothesis 6.168.0 profiles, an evidence lifecycle model, implementation state-machine properties, and fault-injection self-tests.

The optional profiles require this release's source checkout, Python, Node/npm and Java. They are not bundled into the executable. From the source checkout, run `python3 tooling/verification/tools.py setup`, then `.venv/bin/python tooling/verification/tools.py status`. See `docs/harness/verification-tools.md` for execution and prerequisites. Bounded model checks and generated tests do not establish whole-program correctness.

## Install

1. Download the archive matching your OS and CPU, plus its `.sha256` checksum.
2. Verify the checksum and extract the archive.
3. Read `START-HERE.md`, then run `./harnessctl usage agent`.

No external Python is needed by the CLI. Usage, schemas and result validation work offline before repository initialization. Project-specific build/test runtimes remain required for configured capabilities.

macOS binaries are ad-hoc signed; Developer ID signing and Apple notarization are not configured. Windows native is not supported.
