# Harness router

バイナリ利用時の入口: `harnessctl usage agent`。操作一覧は `harnessctl usage commands`、入力契約は `harnessctl schema`。

ユーザーの目的と既存の権限に従う。`.harness/` はmachine-readable control plane、`docs/` は根拠となるknowledge。

- 初回導入・日常利用: [利用開始ガイド](docs/harness/getting-started.md)
- 構造と操作: [operating model](docs/harness/operating-model.md)
- Architecture: [map](ARCHITECTURE.md)、[evolution](docs/evolution/index.md)
- Domain: [index](docs/domain/index.md)、Security: [index](docs/security/index.md)
- 資産: `.harness/assets.json`、チームのpin済みcatalog
- 品質: `.harness/quality.json`、計画: `docs/exec-plans/`

Featureの実装前にTask Contractを作り、`harnessctl preflight --task <path>` を通す。
UNKNOWNを推測で埋めない。capabilityはregistryから選ぶ。
Global awareness, bounded execution: 既存asset・migration・consumerを調べ、変更はTask scopeに限定する。
範囲外の改善は別work itemに記録する。gateの失敗をsemantic判断で上書きしない。
実装後はverify、3視点のsemantic review、delivery checkを行う。
policy・baseline・capabilityの変更はfeatureと分けてレビューする。
