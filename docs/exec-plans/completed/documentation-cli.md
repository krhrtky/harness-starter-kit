# 文書配置規約のCLI導線

Task: `.harness/tasks/documentation-cli.json`（DOCS-CLI-1）。Owner: harness-maintainers。

## 目的と範囲

CLIだけの利用者が、文書配置の基準を取得し、repositoryの正本と同梱の共通規約を区別できるようにする。規約の内容変更、文書の移動、schema・policy変更、リリースは含まない。

## 配置判断

| 対象の問い | 調べた正本・候補 | 主領域／形式 | 操作とpath | 選択根拠・参照影響 | 未決 |
|---|---|---|---|---|---|
| CLIから規約を取得できるか | discovery.pyのGUIDES、配置規約、CLI reference | H13／利用ガイド | 既存usageへdocumentationを登録 | 既存seed本文を表示する。新しい文書取得APIを作らない | なし |
| Agentが適用先を誤らないか | agent-usage.md、bootstrap/intake/plan/learn/garden/review Skills | H13／操作手順 | 既存guideとSkillを更新 | ローカル規約を先に読み、同梱版は共通基準。各Skillへ本文を複製しない | なし |
| 既存導入先を壊さないか | bootstrap.pyのinit/preserved、test_discovery.py | H09／回帰検証 | 既存testへ利用シナリオを追加 | 存在しないroot、保持されたAGENTS/規約、usage本文の取得を実CLIで検証 | なし |

## 実装・証拠計画

1. preflightのreceiptを保持し、usage topic・help・guide・関連Skillの導線を追加する。
2. AC-DISCOVERYは目次からtopicを選び、初期化なしで全文を得る実CLIテストで確認する。
3. AC-ROUTINGはguide/Skillの取得コマンドが解決するテストと、ローカル正本を優先する文章レビューで確認する。
4. AC-PRESERVEは既存AGENTS/規約を持つ一時repositoryをinitし、保持された本文とpreserved結果、同梱規約の取得を確認する。
5. test.unitのEvidenceを作り、各ACとglobal-impactを3視点でレビューしdeliveryで照合する。

## 影響・戻し方

既存のharness.cli、harness.seed、bootstrapを利用する。登録consumerはなく、移行中のtransitionもない。CLIの既存JSON envelopeとexit codeを維持する。qualityの点数は変更しない。

問題時は追加topic、案内、対応テストだけを戻す。既存の規約、ユーザーの未コミット変更、policyやbaselineを取り消さない。

## 保証の境界

実CLIテストは取得・案内・非破壊性を確認する。Agentの実際の意味判断を試す独立実行や、公開済みバイナリの差し替えはこのTaskの保証に含めない。
