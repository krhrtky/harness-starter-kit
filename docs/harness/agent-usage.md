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


## 文書を作る・更新する前

文書の作成・更新・配置整理・網羅性確認は`harness-document`を使う。自動発見されない場合や初期化前は`harnessctl usage harness-document`でSkill全文を取得し、JSONの`content`を読む。判断基準は配置規約、実行手順はこのSkillが担当する。

初期化前でも`harnessctl usage documentation`で配置規約の全文を取得できる。JSONの`content`を読む。このコマンドはCLIに同梱した共通規約を返し、`--root`で指定したrepositoryの文書を読み取るものではない。

初期化後は、ユーザーの明示指示と既存の正本指定を保持し、repositoryの`docs/harness/documentation-policy.md`（またはAGENTS.mdが指定するローカル規約）を先に読む。同梱版でローカル規約を上書きしない。旧版の導入先でローカル規約がない場合は、既存正本を検索し同梱規約を共通の判断基準として使う。矛盾する項目だけを未決として確認する。

規約の「配置を決める順序」に従い、正本・主領域・形式・更新か新規か・選択根拠を計画または変更説明へ記録する。初期化後の登録済み正本は`harnessctl knowledge index`でも確認できる。未登録文書も検索する。迷った項目は候補と影響を示し、未決情報を現行仕様へ昇格しない。

`init`でAGENTS.mdや規約がpreservedになった場合も、この取得コマンドを使える。既存ルールを保ち、配置規約への参照をrouterへ統合する。`knowledge check`の成功は分類・本文の十分性の自動保証ではない。配置規約の網羅性点検と3視点のレビューも行う。

## Versionと権限

binary内のusageはそのCLI versionに対応する。repositoryへ展開した文書は導入先で変更されている場合がある。
CLIの仕様はbinaryのusage/schema、プロジェクト固有の判断はrepositoryのknowledgeを読む。
upgrade時はmigrateの差分とconflictを確認する。usageの取得は実行・変更の権限を増やさない。

新しいSkillを既存導入先へ追加するときは、更新したCLIで`harnessctl migrate`のupdates/conflictsを確認してから`harnessctl migrate --apply`を実行する。ローカル編集されたSkillのconflictは内容を確認して統合し、上書きで解消しない。`init`の再実行では初期化済みrepositoryへ追加されない。
