---
name: harness-bootstrap
description: 空または既存repositoryへHarnessを導入する際に使用する。
---

# Harness bootstrap

repository rootを作業基準とする。別ディレクトリからは `harnessctl --root <repo> ...` を使う。

`harnessctl inspect`で既存の構成とAGENTS階層を確認する。既存文書を先に読む。
`harnessctl init --owner <owner> --mode greenfield|brownfield`を実行する。preserved一覧の既存AGENTSへrouterを統合する。
`.harness/knowledge.json`、interfaces、evolutionにプロジェクトが実際に決めたことだけを記録する。
未決のドメイン・security・SLOはUNKNOWNを残し、必要な決定をユーザーに示す。
inspectのcapability候補は自動有効化しない。プロジェクトの検証コマンドを確認してregistryに接続する。
Brownfieldは`harnessctl baseline`で既存欠損を記録する。`doctor`の結果と未充足項目を提示する。
