# Verification ownership and result contracts

検証機構をどこへ置くか、外部判定をどうdeliveryへ接続するかを定める。構造的な独立性とtoolの知名度だけでは検証の正しさを保証しない。

## 3パターンと評価観点

| 分類 | 主な責任 | 適用対象 | 残る責任 |
|---|---|---|---|
| 独自実装 | Harness／業務固有の意味・関連付け | Taskと証拠、必須capability、鮮度、許可条件、薄いwrapper | 何を正しいとするか、結果の強制、固有規則のtest |
| tool導入 | 独立した専門検証・横断基盤 | model checker、中央static analysis、policy engine、API差分 | model・規則・対象範囲・版・更新・実装との対応 |
| 言語側への委譲 | 対象アプリのcompiler／library／test・build基盤 | 型、schema、property/stateful test、architecture test、暗号 | 業務property、期待値、対象範囲、依存更新 |

言語側には第三者libraryを含む。ArchUnit／Hypothesisをアプリのtest依存にするなら言語側、共通serviceとして運用する機構ならtool側。分類は製品名やCLI形式ではなく所有する層で決める。同じcapability内の規則、engine、wrapperは分けてよい。

以下の観点をADRまたはTaskのasset analysis／計画に記録する。新しいcontrol-plane fieldは要求しない。

- 検証したい性質、入力・操作列・対象言語、保証範囲と範囲外。
- 既存asset、tool、言語機構で再利用できる部分と、自作せずに済む汎用機構。
- 検証器への信頼根拠: 使用機能の文書・test・修正履歴、対象version対応、既知制約。
- 本体との独立性: 同じ関数から期待値を生成していないか。同じ誤った仕様を共有しない確認方法。
- 実装との距離: modelとcodeの対応を何で確認するか。直接codeを検査する方法との役割分担。
- ケース列挙漏れと仕様漏れの区別、bounded探索と生成testの限界。
- 導入・更新・規則/model保守・実行・診断を含む総費用、owner、再現方法。
- 不採用案と、その反証を受けても残る採用理由。

新規欠陥の発見や長期ROIの実証を、限定先行導入の必須条件にはしない。同じ判定になった小さな独自実装があっても、汎用検証器を保守する責任は同じではない。一方、知名度だけで全Task必須化しない。

## 機能の配置

| 機能 | 第一候補 | 固有部分と条件 |
|---|---|---|
| Task／evidence／deliveryの意味 | 独自実装 | 既存Harness Coreを保持。下位のschema・hashを自作しない |
| result検査 | 独自の受入schema＋言語側のjsonschema | parser/validatorは既存実装、意味はschemaのconst/required等で指定 |
| 状態modelの検証 | tool: Quint＋Apalache等 | 汎用探索器を自作しない。model・不変条件・bound・実装との対応は定義する |
| 実装の操作順・不変条件 | 言語側のproperty/stateful test | 実装を直接実行。生成testのPASSを全状態証明と呼ばない |
| 型・unit/integration test | 言語側 | 現行build/testを再利用 |
| architecture依存 | 単一言語は言語側、横断解析はtool | 許可依存・例外・未観測範囲を固有定義。図・indexだけでconformanceを保証しない |
| SAST／fuzzing／mutation | アプリ所有は言語側、中央campaignはtool | 対象言語・欠陥分類・除外を記録。score単独で十分性を判定しない |
| hash・署名 | 言語側の既存primitive | producer／失効／contextの判断は固有。外部証明serviceを選ぶ場合はtool |
| OPA/Rego | 共通policy評価を独立運用するならtool | 単一resultの検査に必須ではない。規則と強制はHarness側に残る |
| OpenAPI/AsyncAPI検査・oasdiff等 | tool、実動作contract testは言語側 | API記述と実consumerの期待は別。Pact等の配布serviceはtoolとして分ける |
| CUE | 設定の制約・合成基盤を選ぶならtool | 単純なJSON Schema検査の置換を必須にしない |
| Structurizr/C4、FRET、DMN/BPMN | 対象model・要求・工程を定めた専門tool | 表現形式や仕様と製品を区別。実行modelと業務・codeの対応は別に検証 |
| RDF/SPARQL/SHACL、OSLC、SCIP | 横断基盤ならtool、局所libraryなら言語側 | 語彙・protocol・formatだけで完全なtrace/依存観測にはならない |

上表は導入位置の選択肢であり、列挙toolの同梱・自動installを意味しない。登録する実行コマンドは対象repoのbuild・lockfile・承認した検証条件から選ぶ。

## 既存process adapterへの接続

1. 対象のbuild/testと`harnessctl inspect`を読み、候補を確認する。候補表示だけで実行しない。
2. 正常・既知の違反・不正入力・実行失敗・timeout/unknownの判定を確認する。property testならseedと失敗入力、model checkerならmodel・tool版・bound・反例を保存する。
3. 失敗を非0へ反映する既存コマンドなら直接登録する。JSON内部に判定があるtoolは薄いwrapperを用意する。
4. wrapperはproducerの非0を保持する。producerが完了した後で受入schemaを検査し、拒否・不明・検証不能を非0へ反映する。producerとcheckerを別capabilityに分けて暗黙の実行順に依存しない。
5. registryへ明示的なargv/cwd/timeout/env/artifactsを登録し、TaskのACから要求する。policy/capabilityの変更はfeatureとは分けてレビューする。
6. 通常のpreflight→verify→semantic review→delivery checkで消費する。任意の先行試験が存在するだけではdelivery必須条件にしない。

## result validate

初期化前のrepoでも利用できる読み取り専用コマンド:

```sh
harnessctl result validate --schema verification/accepted.schema.json --input .harness/runs/tool-result.json
```

`--root`を指定する場合はsubcommandの前へ置く。schemaとinputはrepo相対path。schemaはsource snapshotに含まれる場所に置く。runs/build/cache内のschemaは拒否する。inputは生成物なのでrunsへ置ける。

- exit 0: 与えたJSONが受入schemaを満たす。
- exit 1: 評価が完了しschemaに不一致。`result.mismatch`とJSON pathを返す。
- exit 2: 入力欠損、不正JSON、schema不正、未対応dialect、解決不能な参照など。

schemaはDraft 2020-12を明示する。単一document内の`$defs`/`$ref`を使える。参照先をnetworkや別fileから自動取得しない。使用時に解決不能な参照はexit 2となる。重複JSON memberとNaN/Infinityを拒否する。formatの評価範囲は同梱jsonschema/FormatCheckerがサポートするものに限る。独自formatの保証はwrapper側の専門検査へ委譲する。

例はfixture-v1という固定対象の受入条件であり、全tool共通のenvelopeではない:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "schema_version": {"const": 1},
    "subject": {"const": "fixture-v1"},
    "decision": {"const": "PASS"}
  },
  "required": ["schema_version", "subject", "decision"],
  "additionalProperties": false
}
```

実toolのfieldに合わせて受入schemaを定義する。判定fieldの存在だけを検査するschemaではFAILを拒否できない。空schemaや緩いschemaを用いてもこのコマンドが追加の業務意味を推測することはない。Task/revision/検証parameterの期待値が動的なら、wrapperが独立に取得して照合する。検査される結果自身から期待値を作らない。

wrapperの処理順は次のとおり。言語固有の既存task runnerでも同じ契約を実現できる。

```text
前回の結果を除去、または実行ごとの新しい出力先を用意
producerをargvで実行
producerが非0 → その失敗を返す
producerが0 → result validateを実行してその終了値を返す
```

結果fileをcapabilityのartifactsへ登録する。既存adapterが更新とdigestを記録する。schema・wrapper・lockfile・modelはsource snapshotへ含める。変更後は再verifyする。`result validate`単独のPASSは、producerが今回実行されたこと・結果が新鮮なこと・delivery可能なことを証明しない。freshness・Taskとの関連付けは既存Evidence gateとwrapperの役割である。

## 反証と採用境界

| 案 | 反証 | 採用する範囲 |
|---|---|---|
| 独自実装を最小行数で優先 | 短いコードでも汎用機構の検証・保守責任が残る | 固有規則と薄い接続に限定 |
| 信頼されるtoolをすべて先行必須化 | 適用外・探索限界・導入負担・誤検知もある | 対象・保証・版を固定した限定先行導入 |
| すべて言語側へ委譲 | 分散状態や横断policyは単一アプリだけでは扱えない | 実装に密着する検証を委譲し専門toolで補完 |
| 全tool共通の結果envelope | 既存形式の変換・移行が増え、曖昧なPASSへ意味を潰す | 元の結果を保持し、受入schemaまたは専門wrapperで消費 |
| adapterへcheckerの設定fieldを増やす | 配布schema変更・移行・実行順管理を増やす | 既存argvでwrapperを呼ぶ |
| exit 0だけで常に十分 | JSON内のFAIL/UNKNOWNを成功扱いするtoolがある | exitが論理判定を表す場合のみ直接接続 |
| result validateだけで完全検証 | schemaの記述漏れ、鮮度、modelと実装の乖離を扱わない | 構造＋記述した受入条件の評価に限定 |

検証器を自作しない価値は採用理由になり、新規欠陥発見を先行導入の条件にしない。一方、必須gate化ではowner、実行負担、再現性、失敗処理を確認し、全Task必須化はさらに適用範囲を評価する。

## 参考

- [Quint CLI](https://quint.sh/docs/quint) / [Apalacheのbounded検証](https://apalache-mc.org/docs/tutorials/symbmc.html)
- [Hypothesis stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html) / [ArchUnit](https://www.archunit.org/userguide/html/000_Index.html)
- [JSON Schema evaluator](https://python-jsonschema.readthedocs.io/en/stable/index.html) / [OPA](https://www.openpolicyagent.org/docs)

## 実行可能なprofile

Quint＋ApalacheとHypothesisの固定版セットアップ・実行・capability接続は[tool利用guide](verification-tools.md)を参照する。Core binaryへの同梱ではなくsource checkout用profileとして提供する。
