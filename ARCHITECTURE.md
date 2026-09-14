# Architecture

[Platform design](docs/harness/design.md) / [ADR-001](docs/decisions/ADR-001-distribution.md)

Control planeは`.harness/`、knowledgeは`docs/`、CLIは`src/harnessctl/`、配布正本は`src/harnessctl/resources/`。
判定はmodel/checks/gates、外部実行はadapters、I/Oはstorageに置く。

結果の受入と検証機構の配置: [ADR-003](docs/decisions/ADR-003-verification-delegation.md)。schema評価は既存libraryへ委譲し、tool固有の実行はprocess wrapperに置く。
