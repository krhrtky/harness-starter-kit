# ADR-001: Python CLIとversioned JSONでHarnessを配布する

Date: 2026-09-13。Status: Accepted（初期実装の技術選択）。Owner: harness-maintainers。

## Context

開始ディレクトリには既存repository・言語設定がなかった。
汎用Coding Agentへ27 interface、3 loop、検証と学習手段を提供し、Skillsに機械判定を重複実装させない必要がある。
導入先の仕様・architecture・SLOをStarter Kit側で決めないことも制約となる。

## Decision

Python 3.11以上のharnessctl、JSON Schema Draft 2020-12、seed、10 Skillsを1つのwheelとして配布する。
外部プロジェクトコマンドはprocess adapterに閉じ込め、Task/Evidence/Findingsの契約を共通化する。

## Alternatives

| Option | Pros | Cons |
|---|---|---|
| Python + JSON Schema | subprocess/filesystem/CLIを標準ライブラリで扱える、schema検証を既存実装へ委ねられる | Python環境とjsonschema依存が必要 |
| TypeScript + JSON Schema | npm配布、JSチームの親和性 | 非JSチームにもNode環境が必要 |
| Shell + Markdown | 配布物が少ない | JSON契約・履歴・platform差分の保守が難しい |

## Rationale

既存stackの制約がないため、少数の依存でCLI・fixture・schema・process制御をまとめられるPythonを採用する。
JSONのみを受け入れ、YAML暗黙型変換や複数形式の整合を初期版で扱わない。
3 packageを独立releaseする案は、CLI/seed/Skillsのversionずれを避けるため見送る。コード内のresources境界で将来の分離余地を残す。

## Consequences

導入先はargvで任意言語の検証を接続できる。Coreはadapter未登録でも構造検査できる。
初期版のprocess timeoutはPOSIXに依存し、Windows nativeは追加実装が必要。
構造化semantic findingは真偽の証明や本人認証にはならない。CIの信頼境界とreviewer運用を導入先で定める。
既存repositoryは非破壊initとbaselineで段階導入し、policy変更はfeatureとは別にレビューする。

## Review trigger and references

Windows native需要、独立adapter release、signed team bundle需要のいずれかが生じた時に再検討する。
定期見直し: 2026-12-13。
[Design](../harness/design.md)、[Migration](../harness/upgrades.md)。
