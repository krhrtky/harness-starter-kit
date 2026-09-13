---
name: harness-review
description: 検証済みTaskを構造化された意味論レビューで評価する際に使用する。
---

# Harness review

repository rootを作業基準とする。別ディレクトリからは `harnessctl --root <repo> ...` を使う。

要求と現在のknowledge、実装、Evidence Bundleを改めて読み、実装時の自己説明に依存しない。
`.harness/schemas/findings.schema.json`で各ACおよびglobal-impactについてentailment/contradiction/counterexampleを記録する。
`harnessctl inspect`のsource_digestを各findingに付け、Task指定reviewer名を使う。証拠path・前提・反例・unsupported assumptionsを記録する。
全体影響では再利用判断の妥当性、重複の意味論上の差、target architecture、consumer、quality採点根拠を評価する。
不明はunknown。CLIが確認できるのは形式・網羅性・紐付けで、意味論の真偽ではない。
findingsは`.harness/runs/<task-id>/review.json`に保存する。レビューのためだけにproductを修正しない。
