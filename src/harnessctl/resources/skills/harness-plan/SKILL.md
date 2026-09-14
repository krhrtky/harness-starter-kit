---
name: harness-plan
description: preflightを通したTaskの実装・証拠計画を作る際に使用する。
---

# Harness plan

repository rootを作業基準とする。別ディレクトリからは `harnessctl --root <repo> ...` を使う。

文書の作成・更新・配置整理・網羅性確認は`harness-document`（`harnessctl usage harness-document`で取得）を使い、このphaseのTaskとscopeを引き継ぐ。配置の基準はローカルの正本を優先する。共通規約は`harnessctl usage documentation`で取得できる。

Task Contractとpreflight receiptを読み、ACごとの実装手順とcapability実行を計画する。
既存assetの再利用、配置先、対象consumer検証、rollbackの順序を明示する。
計画はTask scope内のdocs/exec-plansへ保存する。計画保存自体のpathもTask scopeに含める。
scope外のconsolidationは別work itemとし、今回のfeatureで無制限に実行しない。
