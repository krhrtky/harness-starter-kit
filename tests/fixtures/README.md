# Fixture repositories

`valid-small-app/app/`を共通コードとし、各`fixture.json`がrepository overlayを定義する。
`tests/support.py`でinitと設定を行い、`test_fixture_matrix.py`がすべてのfixtureを一時repositoryとして実行する。
重複した100個以上のseed fileを各fixtureへコピーして保守することを避けるため、保存形式はoverlayとする。

- empty-greenfield: seedだけでUNKNOWNを検出
- valid-small-app: preflight→verify→review input→deliveryがpass
- missing-domain / stale-knowledge: knowledge欠損・鮮度
- broken-architecture / broken-contract: architecture文書欠損・実行テスト失敗
- brownfield-legacy: baseline化しても触るdomainのUNKNOWNはblock
- conflicting-docs: reviewerが供給した矛盾findingをdeliveryが拒否
- monorepo:別packageの変更はscope逸脱
- nested-agents: local/override routerを持つrepositoryを保持
- unsafe-command: registry cwdのroot外指定は拒否

nested-agentsはCodexの指示優先順位を再実装しない。conflicting-docsはLLMの矛盾発見能力のテストではない。

```sh
python tooling/fixture.py valid-small-app /tmp/harness-demo
harnessctl --root /tmp/harness-demo preflight --task .harness/tasks/task.json
harnessctl --root /tmp/harness-demo verify --task .harness/tasks/task.json
```

既存destinationへの上書きは行わない。Python interpreter pathはfixture作成環境の実行値を使う。
