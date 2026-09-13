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
