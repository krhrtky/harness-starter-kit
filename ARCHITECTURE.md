# Architecture

[Platform design](docs/harness/design.md) / [ADR-001](docs/decisions/ADR-001-distribution.md)

Control planeは`.harness/`、knowledgeは`docs/`、CLIは`src/harnessctl/`、配布正本は`src/harnessctl/resources/`。
判定はmodel/checks/gates、外部実行はadapters、I/Oはstorageに置く。
