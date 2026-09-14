# Verification delegation integration

Task: VERIFY-DELEGATION-1。Owner/reviewer: harness-maintainers。
Preflight: `.harness/runs/VERIFY-DELEGATION-1/preflight.json`。

## Scope and decisions

既存process adapter、JSON Schema評価器、usage/seed配布を再利用する。比較対象は独自実装、外部tool、言語ecosystemへの委譲。固有の受入判断と汎用機構を分ける。
capability schemaへの任意field追加と全tool共通envelopeは、既存exit契約への追加負担・移行・二重判定を生むため採用しない。`result validate`をtool固有wrapperから呼べる読み取り専用CLIとして追加する。受入schemaは生成結果と分け、source snapshotに含める。

## AC and implementation

- AC-RESULT: results.pyでjsonschemaへ評価を委譲。strict JSON、Draft 2020-12、repo内schema、offline reference、exit 0/1/2を検査する。
- AC-GATE: producer→validatorを順に呼ぶfixtureでpreflight/verify/deliveryを実行。producer失敗、論理FAIL、不正schema/version/subject、古いartifactを拒否する。
- AC-COMPAT: 既存suite、offline discovery、init payloadを検査。guideはresources/seed、Skillsはresources/skillsとlocalコピーを同期する。
- AC-DECISION: ADRと運用guideに3分類、反証、限定先行導入と必須gate化の条件を記録。toolのインストールとguideだけの接続例を区別する。

## Verification and review

既存test.unitを変更せず実行。依存はignored .venvへeditable installし、そのbinをPATHの先頭に置く。先に個別test、次にverifyで全suiteとEvidence Bundle生成。entailment/contradiction/counterexampleをACとglobal-impactごとに記録しdelivery checkを通す。同一Agentの3視点reviewであり独立した第三者reviewとは呼ばない。
policy/baseline/capability定義は変更しない。catalogの既存assetに証拠を追加し、変更したknowledgeのdigestを内容review後に更新する。

## Rollback and deferred work

未公開の追加CLIとguideを戻せば既存process contractへ戻る。登録済みcapabilityの移行は不要。将来result validateを使用したwrapperを戻す場合、論理結果をexitへ反映する代替を先に確保する。
Quint/Hypothesis等の各実対象への接続、鍵運用基盤、未完conformanceは別Taskで対象・保証条件を定める。今回この作業を実施済みとは報告しない。
