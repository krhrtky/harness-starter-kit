---
name: harness-garden
description: repositoryまたはteamの資産・knowledge・品質の継続整備に使用する。
---

# Harness garden

repository rootを作業基準とする。別ディレクトリからは `harnessctl --root <repo> ...` を使う。

文書の作成・更新・配置整理・網羅性確認は`harness-document`（`harnessctl usage harness-document`で取得）を使い、このphaseのTaskとscopeを引き継ぐ。配置の基準はローカルの正本を優先する。共通規約は`harnessctl usage documentation`で取得できる。

`knowledge check`、`quality`、`inventory duplicates`、`eval report`から対象を絞る。
重複候補は同値性の証明ではない。ドメイン意味論・利用者・公開契約を調べ、consumer testで確認する。
cleanupは独立Taskとしてintake/preflight/verify/review/deliveryを通す。次回予定を勝手に作成しない。
lifecycle.schema.jsonでstandard化・廃止・削除のdecisionと全consumer検証を記録し`inventory transition --file <path>`で更新する。
広域移行はcurrent/target/transitionを更新する別計画に分ける。改善後の`baseline`は残存欠損だけへ単調に縮める。
team資産は元のownerへ提案し、ローカルforkや無断のshared policy緩和を作らない。
