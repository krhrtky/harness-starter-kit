# Quint・Apalache・Hypothesisを利用する

このprofileはHarnessのsource checkoutで利用する。Coreの単体binaryにNode/Java/tool本体を同梱する方式ではない。実行入口は`tooling/verification/tools.py`、固定依存は同directoryのpackage-lock.jsonとrequirements.txt。

## セットアップ

前提: Python 3.11以上、Node.js/npm、Java。今回の動作確認はmacOS arm64、Python 3.11.3、Node 20.11.0、Java 21.0.2。runnerのprocess group制御はPOSIX向けで、WindowsはWSLを使う。別OS/版での動作を今回確認したとは扱わない。

repo rootで実行する:

```sh
python3 tooling/verification/tools.py setup
.venv/bin/python tooling/verification/tools.py status
```

setupは`.venv`を作成または再利用し、Harnessをeditable installする。Hypothesis 6.168.0、sortedcontainers 2.4.0、attrs 26.1.0を同環境へ導入する。Quint 0.32.0はnpm lockから`npm ci --ignore-scripts`で導入する。Apalache 0.56.1は公式archiveのSHA-256を確認してから`.venv/verification-tools`へ展開する。globalのPython/npm/Java設定は変更しない。

Quintの推移依存はpackage-lockのintegrityで固定。Pythonのprofile依存はrequirementsで版を固定するが、Harness本体の推移依存まで完全なhash lockにしたわけではない。Node/Javaは検出した実版を各結果へ記録する。

初回setupはPyPI/npm/GitHubへのnetworkが必要。Apalache取得が制限される環境では、同じhashのarchiveを指定できる:

```sh
python3 tooling/verification/tools.py setup --apalache-archive /path/to/apalache-0.56.1.tgz
```

固定hash: `a61c07569d7195ddc589f01037fa10fafef4fb0796af2f1c9cb45226375dfbfc`。正常archiveはlocal cacheへ保存する。破損cacheを自動的に信用して展開しない。setup再実行はmanaged dependenciesを固定版へ戻し、Apalacheのmanaged展開先を置き換える。そこへ独自fileを置かない。

## 実行

```sh
.venv/bin/python tooling/verification/tools.py formal
.venv/bin/python tooling/verification/tools.py properties
.venv/bin/python tooling/verification/tools.py selftest
```

| command | 実行するもの | PASSの意味 |
|---|---|---|
| formal | Quint parse/typecheck、正常受理経路のtest、Apalacheで最大8遷移の検証 | 指定modelとboundで不変条件違反が見つからない |
| properties | Hypothesisで実際のHarness Evidence gateへ生成操作列を実行 | 実行した操作列で独立に管理した期待状態と一致 |
| selftest | freshness guard欠落modelと、鮮度findingを除外した実装側fault injection | 意図した両欠陥を検出した。欠陥対象そのものがPASSした意味ではない |

各コマンドはtool版を確認する。正常受理経路のQuint testは同梱TypeScript evaluatorを明示し、Rust evaluatorの自動取得を避ける。Apalacheのmodel検査とは役割を分ける。run時の暗黙installや別backendへのfallbackはない。このprofileは両toolchainをまとめてstatus確認するため、propertiesだけを実行する場合もsetupを先に完了させる。

外側の終了値は0=成功、1=tool検証の拒否、2=実行不能・設定不正等。producer非0をPASSへ変換しない。selftestは期待した種類の反例・assertionだけを成功とし、構文エラー・依存欠損を期待REDとして受け入れない。

## 検証対象

`verification/evidence.qnt`はEvidence受入の有限model。revisionを0〜2、verifiedRevision、検証成功、log整合性、直近の受入判定で表す。操作はsource変更、検証成功・失敗、log改変、受入判定。操作が変わると直近の判定をresetし、過去のdelivery後の変更を不正な過去判断として扱わない。

不変条件は「受理されたなら、成功した証拠で、logが整合し、検証対象revisionが現在と一致する」。正常経路はinit→verifyPass→acceptEvidenceで実際に受理へ到達することをQuint testで確認する。selftestは受入条件からrevision一致だけを除去し、staleな証拠の受理をITF traceで確認する。

`tooling/verification/properties.py`は一時repoを作り、実際の`verify`／`evidence_checks`を呼ぶ。検証成功・失敗、source変更、log改変をHypothesisが組み合わせる。期待するfresh/intact/passは操作から独立に更新し、本体の判定から作らない。

設定: max_examples=25、stateful_step_count=12、derandomize=True、database=None、deadline=None。25は設定上限であり、必ず異なる25列・300操作を検査したと主張しない。version・同じtestコード・設定によって再現し、失敗時の縮小された操作列はlogに残る。freshness fault injectionは結果から`evidence.stale`を除外する試験で、productionコードを書き換えない。

modelと実装で同じ性質を確認するが、自動変換の等価性証明ではない。Task binding、全semantic review、署名、全delivery条件をこのmodelが網羅するわけではない。Hypothesisの生成testは全状態証明ではない。

## 自分のQuint modelを検証する

```sh
.venv/bin/python tooling/verification/tools.py formal --model verification/my-model.qnt --main MyModel --invariant myInvariant --max-steps 12
```

modelはrepo内のfileで、`init`と`step`を持たせる。importを含む複数file modelはこの単一file実行profileの対象外で、既存project runnerを別capabilityとして登録する。model・不変条件・boundはTaskで決める。default以外のmodelに正常到達testを自動生成しない。

## 結果とHarness接続

実行ごとの結果・生log・反例は`.harness/runs/verification-tools/<run-id>/`に保存する。最新summaryは`formal.json`、`properties.json`、`selftest.json`。新しい失敗は以前のPASS summaryをERROR/FAILで置き換える。実行中断時に古いsummaryが残ってもprocessが成功しないため、Harnessはpassing evidenceとしない。同じprofileを同一checkoutで同時実行しない。

接続するcapabilityは`verify.formal`と`verify.properties`。既存`test.unit`も維持する。registryは次のargvをprocess adapterで実行し、対応する最新summaryをartifactとして保存する:

```json
{
  "id": "verify.formal",
  "adapter": "process",
  "argv": [".venv/bin/python", "tooling/verification/tools.py", "formal"],
  "cwd": ".",
  "timeout_seconds": 300,
  "enabled": true,
  "env": {"HARNESS_MANAGED_PROCESS_GROUP": "1"},
  "artifacts": [".harness/runs/verification-tools/formal.json"]
}
```

propertiesはid・最後のargv・artifactをpropertiesへ置換する。Harness内ではこのenv指定により子toolをadapterのprocess group内に保持する。timeout時はgroup全体を停止し、途中のPASS summaryで成功扱いしない。この場合はsignalによる非0終了になる。envを手動のshellへ常設しない。selftestはtoolchainやモデルの変更時に実行する故障検出確認であり、通常Taskが欠陥modelを検証してPASSしたかのようなcapabilityにはしない。

接続後の利用確認Task:

```sh
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m harnessctl verify --task .harness/tasks/verification-tools-enabled-v2.json --ci
```

同Taskは今回の状態でpreflight済み。sourceやTaskを変更して次の開発に使う場合は、新しいTask IDでpreflightし、AC／required_capabilitiesに必要な検証を対応させる。登録済みでも要求していないTaskへ自動的に全toolを強制する設定ではない。

## トラブルシュートと更新

- runtime欠損: statusのERRORを読み、Node/npm/Javaを用意してsetupを再実行する。
- version不一致: setupで固定版へ揃える。通常runが勝手に最新版へ更新することはない。
- archive hash不一致: 公式の同じreleaseを取得し直す。期待hashを実物に合わせて変更しない。
- parse/typecheck失敗: 当該runのlogを読む。invariant反例とは区別する。
- formal拒否: counterexample.itf.jsonとverify.logを読み、model・仕様・実装のどこに差があるか判断する。
- property拒否: properties.logにある失敗操作列を再現し、仕様と実装を確認する。
- timeout: 検証不能でありPASSではない。対象範囲やboundの変更は保証範囲の変更としてレビューする。

更新時は固定版・lock・hashを明示して変更し、setup→status→formal/properties→selftestを実行する。capability／policyの更新はfeatureと分けてレビューする。

[3分類・結果契約](verification.md)、[Quint CLI](https://quint.sh/docs/quint)、[Hypothesis stateful](https://hypothesis.readthedocs.io/en/latest/stateful.html)。
