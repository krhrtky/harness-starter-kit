# CLI reference

すべてのcommandはJSONをstdoutに出力する。exit 0=成功、1=gate blocker、2=入力/設定/実行基盤エラー。
引数構文の誤りはargparseがstderrへusageを出しexit 2。`--ci`は同じ判定をCIの契約として明示するflag。
`--root <directory>`はsubcommandより前に置く。path引数はすべてrepository root相対。

| Command | 操作 |
|---|---|
| `usage [TOPIC]` | オフラインの目次・guide・Skill全文。commandsは実parser由来の引数一覧 |
| `schema [NAME]` | 初期化前にも入力契約を取得。省略時は一覧 |
| `init --owner TEAM --mode greenfield` | seed/Skills/schemaを配置。既存文書は保存 |
| `inspect` | 技術候補、AGENTS階層、source digest。実行・自動有効化なし |
| `doctor` | 全control plane、参照、knowledge、enforcementの検査 |
| `inventory list` | local + pin済みteam assets |
| `inventory search --capability NAME` | provides一致を検索。複数flag可 |
| `inventory duplicates` | 同じcapabilityを提供するactive assetの候補 |
| `inventory transition --file REQUEST` | schemaに従うlifecycle変更 |
| `preflight --task TASK` | 実装前gate。成功receiptは`.harness/runs/<id>/preflight.json` |
| `check --ci` | 構造gate。brownfield baselineを考慮 |
| `check --phase delivery --task TASK --bundle BUNDLE --findings FINDINGS --ci` | deliveryの全gate |
| `verify --task TASK --ci` | 必要capability実行。bundle pathを返す |
| `evidence validate --task TASK --bundle BUNDLE` | 形式、binding、鮮度、capability、artifact integrity |
| `knowledge index` / `knowledge check` | progressive discovery / knowledge検査 |
| `quality [--against FILE]` | 全scopeの品質比較。既定はcurrent baseline |
| `feedback add --file FILE` / `feedback list` | feedback記録と参照 |
| `feedback propose --id ID` | deterministic/recurrence/categoryから介入候補を分類 |
| `promote --id ID --target PATH --reviewed-by OWNER --decision PATH` | 実在する成果物へのreview済み関連付け |
| `baseline` | 初回capture / 後続は欠損縮小と品質・readiness非劣化のみ |
| `migrate [--apply]` | 既定dry-run、apply時backup。v0からv1とseed差分更新 |
| `eval add --file FILE` / `eval report` | Agent/Harness結果の観測レコードと集計 |

## Delivery example

```sh
harnessctl preflight --task .harness/tasks/feature.json
harnessctl verify --task .harness/tasks/feature.json --ci
```

返却された`bundle`を使い、reviewerが`.harness/runs/<task>/review.json`を作成する。

```sh
harnessctl evidence validate --task .harness/tasks/feature.json --bundle .harness/runs/TASK-1/EV-.../evidence.json
harnessctl check --phase delivery --task .harness/tasks/feature.json --bundle .harness/runs/TASK-1/EV-.../evidence.json --findings .harness/runs/TASK-1/review.json --ci
```

`EV-...`は例示。実際にはverifyの出力値を使う。CLIはreviewのpassを自動生成しない。
Task scopeには修正するdocs、テスト、catalogも含める。runtime evidence/reviewはruns配下へ保存する。
policyやcapabilityの変更が必要ならfeature着手前に設定変更としてレビューする。

## Quality and knowledge updates

quality scoreは定義した評価基準に従って採点し、`basis`と`evidence`を記録する。
knowledgeのレビュー後は`status`、timezone付き`reviewed_at`、ファイルbytesのSHA-256を更新する。
更新日だけでは内容が一致した証明にならないため、digestも照合する。
日付・点数・readinessをgate通過目的で引き上げず、semantic reviewで根拠を確認する。

## Capability adapter

```json
{
  "id": "test.unit",
  "adapter": "process",
  "argv": ["python", "-m", "unittest", "discover", "-s", "tests"],
  "cwd": ".",
  "timeout_seconds": 300,
  "enabled": true,
  "env": {},
  "artifacts": []
}
```

argvはshell文字列ではない。環境変数はPATH/HOME/TMPDIR/SYSTEMROOT/LANG/LC_ALL/VIRTUAL_ENVのみ引き継ぎ、envを追加する。
生成artifactは`.harness/runs/`へ出力する。source fileを更新するtestはstable_source gateで落ちる。
長時間daemonやdev serverは検証用capabilityにせず、完了するhealth-check commandを登録する。
