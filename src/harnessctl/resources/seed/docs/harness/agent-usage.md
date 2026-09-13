# Agent entrypoint for the binary distribution

ソースコードやGitHub閲覧がなくても、実行するCLIと同じversionの手順を取得できる。
最初に`harnessctl --version`と`harnessctl usage`を実行する。usage/schemaはrepositoryやnetworkがなくても動作する。

```sh
harnessctl usage agent
harnessctl usage commands
harnessctl usage harness-bootstrap
harnessctl schema task
```

usageはJSON。topic本文は`content`にMarkdownとして返る。
commands topicは実際のparserからcommand名・引数・必須flag・choicesを返す。
条件付き必須引数（例: deliveryのtask/bundle/findings）は`usage cli`を併せて読む。
schemaは`schema`fieldにDraft 2020-12の定義を返す。関連schemaは`harnessctl schema`で列挙できる。

## 初期化前

CLIがまだない場合は、GitHub ReleaseのSTART-HERE.mdに従ってOS/CPUに合うarchiveを取得する。
CLIがPATHにない場合は絶対pathで実行する。ネットワークから最新手順を推測せず、そのbinaryのusageを読む。
`usage harness-bootstrap`に従ってinspect/initを進める。初期化に必要なownerや未決の仕様はユーザーへ確認する。

## 初期化後

root AGENTS.mdを読み、repositoryのknowledge・policy・capabilityを参照する。
`init`は`.agents/skills/`と`docs/harness/`へ同梱の手順を展開する。AgentがSkillsを自動発見しない場合も、`usage harness-intake`などで全文を取得できる。
既存AGENTS.mdは自動上書きしない。preservedを確認し、既存ルールを保ってusage入口を統合する。

Featureはintake→preflight→plan→implement→verify→review→deliver。
手順に不明点があれば`usage harness-<phase>`を読み、入力形式は`schema <name>`で確認する。
exit 1を成功へ読み替えない。exit 2は入力や環境設定を修正する。

## Versionと権限

binary内のusageはそのCLI versionに対応する。repositoryへ展開した文書は導入先で変更されている場合がある。
CLIの仕様はbinaryのusage/schema、プロジェクト固有の判断はrepositoryのknowledgeを読む。
upgrade時はmigrateの差分とconflictを確認する。usageの取得は実行・変更の権限を増やさない。
