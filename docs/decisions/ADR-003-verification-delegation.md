# ADR-003: 検証機構を委譲し、結果の受入を明示する

Date: 2026-09-14。Status: Accepted。Owner: harness-maintainers。

## Context

Harness、SDLC、Architecture Vaultの比較では、汎用toolの利用価値と独自の受入規則を分ける必要があった。既存process adapterは任意のargvを実行できるが、exit 0とJSON内部の論理PASSが常に同じとは限らない。独自BFSとQuintが有限fixtureで一致しても、独自検証器の保守が有利とは証明していない。

ユーザーは3パターンを比較・反証したうえでHarnessへの統合を依頼した。このADRはその範囲で選択した機構と運用判断を記録する。個別の外部toolを全Taskに必須化する決定ではない。

## Decision

固有の意味・関連付け・受入判断をHarnessに残し、汎用の専門解析はtool、実装に密着した検証は対象言語の既存機構へ委譲する。知名度・実装行数・新規欠陥数だけで選ばず、検証器の信頼根拠、保守責任、実装との距離、独立性、保証範囲、総費用を評価する。

既存process adapterを維持し、`harnessctl result validate`を追加する。repoが所有するDraft 2020-12の受入schemaを既存jsonschemaで評価する。tool固有wrapperがproducer失敗を保持し、結果を検査してexitへ反映する。全toolへ独自envelopeを強制しない。

## Alternatives and rebuttal

| Option | Benefit | Counterargument / decision |
|---|---|---|
| 独自の汎用checker・model探索を標準化 | 局所fixtureなら小さい | 自作機構の正しさ・更新・保守責任を追加する。比較実験用の実装と標準基盤を区別し不採用 |
| 外部tool一括・必須導入 | 再発明回避と共通化 | 適用対象・版・保証限界を無視できない。限定先行導入は許容、全Task一律化はしない |
| 全部をアプリ言語へ移す | 実装との距離が近い | 横断policyや独立modelの検証には別機構も必要。適用範囲を限定 |
| capability schemaへresult fieldを追加 | adapter内に集約可能 | 既存exit型capabilityにも移行・schema保守を課す。現段階ではwrapperで実現できるため不採用 |
| 共通result envelopeを義務化 | 一定の集約形式 | 各toolの意味を変換で失い、wrapper責任は消えない。元artifactを保持 |
| wrapperごとにJSON Schema検査を自作 | 新しいCLI不要 | binary利用者を含め同じ受入検査を再利用できない。既存libraryを使うCLIを提供 |
| exit 0のみ | 現行testでは十分な場合がある | 論理FAILを0で返すtoolでは不足。必要なwrapperにだけresult検査を適用 |

## Rationale

機構の独自実装を減らしながらHarnessのgeneric process契約と既存Taskを維持できる。JSON Schema評価は既存依存を使い、専用policy DSLやmodel checkerをCoreに持たない。source内の受入schemaと生成artifactを分けるため、既存のsource digestとartifact freshnessを利用できる。

## Consequences

正常なexit型testに変更は不要。wrapperは生成物の使い回しを防ぎ、producerとcheckerの失敗を保持する。schemaの記述漏れ、対象との対応、timeout、toolの更新は依然としてownerの責任である。単独result PASSはdelivery許可ではない。

新しいコマンドは明示的なDraft 2020-12と単一documentの参照を扱い、networkや別fileの自動取得はしない。利用者は外部参照のあるschemaを単一documentへまとめるか、既存の専門validatorを直接接続する。format拡張や署名・動的contextは専門wrapperへ委譲する。

## Validation and rollout

Task VERIFY-DELEGATION-1の受入testで、正常、論理FAIL/UNKNOWN、版・対象違い、JSON不正、producer非0、欠損・古い結果、source変更、参照解決不能、path逸脱を検証する。guideとSkillsは配布正本とlocalを同期し、offline usageとinitで検査する。

policy・baseline・enabled capabilityは変更しない。既存登録の移行は不要。採用wrapperの撤回時は代わりの論理判定を先に確保する。新しいCLIの単なる削除でチェックを省略しない。

## Remaining decisions

Quint/Hypothesis等の個別profileの実対象、鍵運用、未完architecture conformanceはその対象Taskで決める。今回toolの追加install・全Task必須化・SDLC/Vault廃止は実施しない。

見直し条件: wrapper間で受入処理の重複が拡大する、共通envelopeを必要とするconsumerが決まる、別dialect/複数file schemaの実需要が確認される。

[運用と3分類](../harness/verification.md)、[ADR-001](ADR-001-distribution.md)、[ADR-002](ADR-002-binary-discovery.md)。
