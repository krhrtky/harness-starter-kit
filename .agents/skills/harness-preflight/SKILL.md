---
name: harness-preflight
description: 既存Task Contractの実装前gateとUNKNOWNを解決する際に使用する。
---

# Harness preflight

repository rootを作業基準とする。別ディレクトリからは `harnessctl --root <repo> ...` を使う。

`harnessctl preflight --task <path>`を実行し、code/path/interfaceごとのblockerを扱う。
機械エラーはCLIを修正または入力を訂正して解決する。semantic判断でpassに変えない。
UNKNOWNはauthoritative knowledgeを読み、前提欠落・矛盾・根拠不足を特定する。
資産検索、配置、migration方向、consumer、証拠計画の意味を確認する。
この段階ではproduct codeを書かない。成功したreceiptを保持し、baselineを取り直して失敗を隠さない。
