---
name: harness-adapt
description: 未接続の技術スタックの検証capabilityをHarnessへ接続する際に使用する。
---

# Harness adapt

repository rootを作業基準とする。別ディレクトリからは `harnessctl --root <repo> ...` を使う。

`harnessctl inspect`の候補と既存build/test設定を読む。候補だけでコマンドを実行しない。
capabilities.schema.jsonに従ってprocess adapterへargv/cwd/timeout/env/artifactsを登録する。
shell文字列ではなくargvを使い、ホストの権限内で検証する。Coreへframework判定を混ぜない。
構造チェックはadapterなしで動く。Taskが要求するcapabilityが未接続ならblockを維持する。
新adapterはAdapter protocolに実装し、失敗・timeout・artifact欠落・source変更のcontract testを加える。

## 検証機構の配置

`harnessctl usage verification`または`docs/harness/verification.md`を読む。機能を独自実装・tool導入・言語側への委譲に分け、既存機構、信頼根拠、独立性、実装との距離、保証範囲、保守責任、反証をasset analysisの理由と計画へ記録する。短い独自実装との結果一致だけでtoolを不採用にしない。限定先行導入と全Task必須化を分ける。

exitが論理判定を表す既存コマンドはそのまま使う。JSON内部に判定を返すtoolにはproducerの失敗を保持するwrapperを用意し、repo所有の受入schemaを`harnessctl result validate --schema <path> --input <path>`で検査する。schemaはsourceへ、生成結果はartifactsへ配置する。動的な対象・parameterの照合はwrapperで行う。結果から期待値を生成しない。正常・拒否・UNKNOWN・不正入力・producer失敗・古いartifactでgateまで確認する。
