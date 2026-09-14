# ADR-004: QuintとHypothesisを実行可能なprofileとして接続する

Date: 2026-09-14。Status: Accepted。Owner: harness-maintainers。

## Context

ADR-003で検証機構の配置とresult受入境界を統合した。ユーザーからtoolを実際に利用できるところまでのサポートが求められた。Harnessの状態判定はPythonで実装され、既存SDLCには固定Quint toolchainの実行実績がある。

## Decision

Quint 0.32.0＋Apalache 0.56.1を有限Evidence modelへ、Hypothesis 6.168.0を実装のEvidence gateへ接続する。setup/status/formal/properties/selftestをsource checkout用profileとして提供し、既存process adapterへ登録する。

modelはfreshness・検証成功・log整合性に限定する。生成testは実装へ操作列を与える。model checkerやtest生成器を独自実装しない。正常受理経路と意図したguard欠落の検出を両手段で確認する。

## Alternatives and rebuttal

| Option | Benefit | Counterargument / decision |
|---|---|---|
| guideだけ | 追加環境不要 | 実行・失敗確認・接続が利用者へ残るため今回の要求に不足 |
| toolをCore binaryへ同梱 | 単一配布 | Node/Java・言語依存がCoreへ入り、他projectにも負担を課す。source profileを採用 |
| Quintのみ | 設計状態を検査 | modelと実装の乖離は残る。実装を直接呼ぶ生成testで補完 |
| Hypothesisのみ | 実装へ近い | 生成した操作列以外の保証はない。有限modelのbounded検査を併用 |
| 全catalog toolの導入 | 広い選択肢 | API/工程/対象言語などの入力がないtoolまで意味ある検証を用意できない |

## Consequences

global runtime設定を変えずlocal .venv/node_modulesへ導入する。sourceを持たないbinary-only利用者にはprofileのsource取得が必要。runtimeと規則の保守費用は残る。

modelと実装の等価性証明ではなく、限定された共通の性質を異なる方法で確認する。toolを登録しただけで全Task必須にはしない。必要なACへ要求を対応付ける。

## Validation and rollout

VERIFY-TOOLS-1で機構・モデル・生成testを検証する。capability登録は別の設定review後、VERIFY-TOOLS-ENABLED-1で接続を確認後、Quint testの既定Rust取得を見つけたため、TypeScript evaluatorを明示するVERIFY-TOOLS-ENABLED-2でtest.unitと両profileのEvidence Bundle、review、deliveryを確認する。依存欠損、timeout、producer非0、偽の期待反例をPASSにしない受入testを持つ。

見直し条件は対象modelの拡大、複数file import、runtime変更、生成testの実行負担、別言語のconsumer追加。

[利用手順](../harness/verification-tools.md)、[ADR-003](ADR-003-verification-delegation.md)。
