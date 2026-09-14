---
name: harness-intake
description: feature要求をHarness Task Contractに変換する際に使用する。
---

# Harness intake

repository rootを作業基準とする。別ディレクトリからは `harnessctl --root <repo> ...` を使う。

文書の作成・更新・配置整理・網羅性確認は`harness-document`（`harnessctl usage harness-document`で取得）を使い、このphaseのTaskとscopeを引き継ぐ。配置の基準はローカルの正本を優先する。共通規約は`harnessctl usage documentation`で取得できる。

`.harness/schemas/task.schema.json`に従いTask Contractを作る。ユーザーのoutcome、非目標、AC、risk理由を保持する。
`harnessctl inventory search --capability <capability>`で必要能力を検索し、すべての候補にreuse/extend/distinctの根拠を記録する。
既存の関連実装とplanned/active migrationを読む。placement、target alignment、consumer impactを記録する。
scopeは実装・テスト・knowledge・catalog更新に必要なpathだけ。広域改善はnon_goalsと別work itemに分ける。
ACには実行するcapabilityを対応付け、reviewerを特定する。未解決はunknownsに残す。
Task JSONはpreflight前に保存する。receipt発行後にTaskを変更する場合は新しいtask IDを使う。
