# All IN Harness Starter Kit

Coding Agent向けにTask Delivery、Repository Evolution、Team Evolutionの3ループを提供するPython製Harness Platform。
H00–H16をDelivery Interfaces、H17–H26をEvolution Interfacesとして扱う。

**開発の考え方は[Harnessが支える開発プロセス](docs/harness/development-process.md)を参照してください。**
目的と変更範囲の共有、証拠に基づく完了判断、学びを次の開発へ戻す流れを説明しています。

導入する場合は[利用開始ガイド](docs/harness/getting-started.md)を参照してください。
ユーザー向けセットアップ、Agentへの依頼例、Agentの入口と完了条件をまとめています。

GitHub Releases向けにPython不要のmacOS/Linuxバイナリを提供します。
[バイナリ配布と導入](docs/harness/releases.md)を参照してください。wheelによる導入も利用できます。
開発・wheel導入にはPython 3.11以上と`jsonschema`を使用します。バイナリ利用者はPythonを用意する必要がありません。Coreの構造検査はproject adapterなしで実行できる。

バイナリを受け取ったら、まず以下を実行します。usage/schemaはオフラインで使えます。

```sh
./harnessctl usage
./harnessctl usage agent
./harnessctl usage commands
./harnessctl schema task
```

ソースから導入する場合:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/harnessctl --root /path/to/repo init --owner team-name --mode brownfield
.venv/bin/harnessctl --root /path/to/repo inspect
```

initは既存文書を保存する。seedはプロジェクト固有仕様をUNKNOWNとして生成する。
`doctor`で不足を確認し、knowledge・target architecture・capabilityを接続する。
Brownfieldでは`baseline`を記録してから、触るinterfaceを要求readinessへ改善する。

- [実行例とCLI](docs/harness/cli.md)
- [設計と責務](docs/harness/design.md)
- [アップグレードと移行](docs/harness/upgrades.md)
- [検証方法と限界](docs/harness/validation.md)
- [導入サンプル](examples/README.md)

```sh
python -m unittest discover -s tests -v
```
