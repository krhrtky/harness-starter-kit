# Runnable examples

repositoryをvenvにinstallした状態で以下を実行する。`/tmp/harness-demo`は未作成のpathを選ぶ。

```sh
python tooling/fixture.py valid-small-app /tmp/harness-demo
harnessctl --root /tmp/harness-demo inspect
harnessctl --root /tmp/harness-demo doctor
harnessctl --root /tmp/harness-demo inventory search --capability order.cancel
harnessctl --root /tmp/harness-demo preflight --task .harness/tasks/task.json
harnessctl --root /tmp/harness-demo verify --task .harness/tasks/task.json
```

receiptとbundleは`.harness/runs/TASK-1/`に生成される。
`.harness/schemas/findings.schema.json`を参照してレビュー結果をruns配下へ保存し、[delivery command](../docs/harness/cli.md)を実行する。
テストfixture用のpass findingを実プロジェクトのreviewとして転用しない。

Brownfieldは`python tooling/fixture.py brownfield-legacy /tmp/harness-legacy`で再現できる。
`check`は既存負債を許容し、Taskの`preflight`は触るdomainのUNKNOWNをblockする。

## Team snapshot

`team.schema.json`のname/assets/policy/evolutionを`.harness/team.json`に保存する。
projectの`team_bundle`をそのpath、`team_digest`をcanonical JSONのSHA-256にする。

```python
from harnessctl.storage import digest, read
print(digest(read('.harness/team.json')))
```

文字列のpinはデータの固定であり、署名検証やネットワーク同期ではない。
team assetはlocal assetに合成されるため、同じcapabilityの検索でcross-repo assetが見つかる。
