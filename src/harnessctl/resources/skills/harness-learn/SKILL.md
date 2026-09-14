---
name: harness-learn
description: deliveryや障害の学習を既存asset・tool・knowledgeへ反映する際に使用する。
---

# Harness learn

repository rootを作業基準とする。別ディレクトリからは `harnessctl --root <repo> ...` を使う。

文書の作成・更新・配置整理・網羅性確認は`harness-document`（`harnessctl usage harness-document`で取得）を使い、このphaseのTaskとscopeを引き継ぐ。配置の基準はローカルの正本を優先する。共通規約は`harnessctl usage documentation`で取得できる。

root cause、再発性、既存rule/assetを調べ、abstraction修正・test・rule・skill・knowledge・介入なしを比較する。
feedback.schema.jsonを作り、`harnessctl feedback add --file <path>`と`feedback propose --id <id>`を使う。
CLIの候補は分類支援。意味論と採用理由はfeedbackに記録し、既存資産で解決するなら新ruleを増やさない。
実際の成果物とdecisionを作り、policyのreviewer確認を記録した後に`promote --id <id> --target <path> --reviewed-by <owner> --decision <path>`を使う。
promoteは関連付けであり、実装・効果確認の代わりにならない。eval schemaで観測結果を記録し`harnessctl eval add --file <path>`を実行する。
