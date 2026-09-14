# Executable verification tools

Task: VERIFY-TOOLS-1。Owner: harness-maintainers。

## Plan

1. 既存Quint 0.32.0/npm lockと検証済みApalache 0.56.1の配布hashを再利用し、Harness内へ独立したセットアップを提供する。Node/Javaは既存runtimeを利用し、依存と展開物をlocal .venv/node_modulesへ隔離する。
2. Evidence acceptanceの有限状態modelを定義する。正常到達をQuint testで確認し、bounded verifyとfreshness guard欠落の反例で機能確認する。
3. Hypothesis 6.168.0で実装のevidence_checksへ操作列を与える。正常・source変更・log改変・検証失敗を操作に含め、欠落guardのfault injectionが失敗することを確認する。
4. setup/status/formal/properties/selftestを一つのsource-checkout用入口へまとめ、実行ごとの記録をrunsへ保存する。失敗時に以前のPASSを使わない。
5. 単体contract tests、実tool試験、verify/review/deliveryを行う。capability登録はこのfeatureの後に別の設定reviewとして行い、接続済みTaskでもverifyする。

## Assets and limits

汎用process、jsonschema、既存test fixtureは再利用する。追加assetはtooling/verification。modelの探索器や生成test engineは独自実装しない。
同じ性質をmodelと実装で確認するが、変換等価性の形式証明ではない。modelはTask/署名/全delivery制約を網羅しない。

## Rollback

登録capabilityを必要とするTaskを先に見直し、別の設定変更として無効化する。依存を消してPASSへ変換するfallbackを作らない。元のSDLC/Vaultと以前の実験証拠は保持する。
