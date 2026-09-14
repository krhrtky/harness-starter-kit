# 利用開始ガイド

Harnessは、Coding Agentが既存資産と制約を確認して実装し、証拠を残して完了するための共通基盤です。
利用者は目的とプロジェクト固有の決定を伝え、AgentはSkillsとCLIを使って作業します。

開発全体の考え方と役割分担は、[Harnessが支える開発プロセス](development-process.md)を先に参照してください。

## 1. CLIを実行環境へ導入する

GitHub ReleasesからOS/CPUに一致するarchiveを取得し、checksumを確認して展開します。
START-HERE.mdを読み、`./harnessctl usage agent`を実行してください。Pythonの導入は不要です。
詳しくは[バイナリ配布手順](releases.md)を参照してください。

wheelで導入する場合はPython 3.11以上を用意します。以下はmacOS/Linuxの例です。
wheelのpathは受け取った実ファイルの場所に置き換えます。

```sh
python3 -m venv .harness-cli-venv
.harness-cli-venv/bin/python -m pip install /path/to/harness_starter_kit-1.2.1-py3-none-any.whl
.harness-cli-venv/bin/harnessctl --version
```

このvenvは対象repositoryの外に置きます。既存プロジェクトの依存関係へHarnessを混ぜる必要はありません。
以降の例では、このCLIのディレクトリにPATHが通っているものとします。
PATHを変更しない場合は、`harnessctl`をインストールした実行ファイルの絶対pathに置き換えてください。

CLIの導入は実行環境ごとに必要です。同じ端末で複数repositoryを扱う場合は共用できます。
CI runnerや別ホストで動くAgentには、その環境にも同じversionを導入します。
Agentへ導入を依頼することはできますが、Skillsを配置するだけでCLIが自動インストールされるわけではありません。

## 2. Repositoryを初期設定する

既存repositoryでは次を実行します。新規repositoryではmodeをgreenfieldにします。

```sh
harnessctl --root /path/to/repo inspect
harnessctl --root /path/to/repo init --owner team-name --mode brownfield
harnessctl --root /path/to/repo doctor
```

initは`.harness/`、knowledge文書、router、11 Skillsを配置します。既存文書は上書きしません。
既存AGENTS.mdがある場合は、initのpreserved一覧を確認してHarness routerを統合します。
直後のdoctorがUNKNOWNを報告するのは、プロジェクト固有の決定が未設定だからです。

| 利用者・チームが決めること | Agentが補助する作業 |
|---|---|
| outcome、非目標、受け入れ条件 | Task Contractへの整理 |
| domain invariant、target architecture、権限 | 既存文書の探索、未決事項の抽出、knowledge整理 |
| 使用するbuild/test command | capability registryへの接続と動作確認 |
| 品質の評価基準とowner | quality/asset catalogの登録 |

Brownfieldでは既存欠損を確認して`harnessctl baseline`を実行します。
その後、最初に変更するinterfaceからUNKNOWNを解消します。baselineは新しい欠損を許すための操作ではありません。
初期設定はrepositoryに保存して共有し、メンバー全員が初めから作り直すことを避けます。

## 3. ユーザーからAgentへの依頼例

初回導入:

> このrepositoryにHarnessを導入してください。harness-bootstrapを使い、既存文書とコマンドを調べ、未決の仕様だけを確認してください。

Feature実装:

> 注文キャンセル機能を実装してください。harness-intakeから始め、既存assetを検索し、preflight、実装、verify、review、delivery gateまで進めてください。

資産の整備:

> harness-gardenを使って重複assetと古いknowledgeを調べ、根拠のある改善候補を示してください。今回の変更範囲を決めてからcleanupを実行してください。

ユーザーが日常的にすべてのJSONを書く必要はありません。Agentが整理し、未決の業務判断はユーザーへ確認します。

## 4. Agentの入口と完了条件

Agentはroot AGENTS.mdからknowledgeと該当Skillへ進みます。
CLIが見つからない場合は、実行環境のインストール先を確認します。検証を省略して完了扱いにしません。

| 状況 | Skill | CLI / 出力 |
|---|---|---|
| 初回導入 | harness-bootstrap / harness-adapt | inspect、init、doctor、capability |
| 要求整理 | harness-intake | Task Contract、asset検索、UNKNOWN |
| 実装前 | harness-preflight / harness-plan | preflight receipt、範囲内の計画 |
| 実装後 | harness-verify / harness-review | Evidence Bundle、3視点のfinding |
| 完了判定 | harness-deliver | delivery checkのpass |
| 学習・整備 | harness-learn / harness-garden | feedback、改善Task、lifecycle、ratchet |

構造チェックのpassだけでfeature完了とはしません。
Taskごとの証拠とsemantic findingを揃え、delivery checkを通してから結果を報告します。
CLIのJSON結果は`ok`と`findings`を確認します。exit 1はblocker、2は入力や設定のエラーです。

## 5. Pythonとバイナリ配布

Python実装を維持し、PyInstallerでPython・依存関係・usage・schema・seed・Skillsをまとめた単体実行ファイルを生成します。
`harnessctl usage`と`harnessctl schema`はソースcheckoutなしで取得できます。
その場合、利用者によるPythonの導入は不要ですが、配布側はOS・CPUに合わせてbuild/testを用意します。
単一file方式には起動時の展開処理があります。[PyInstaller公式説明](https://pyinstaller.org/en/stable/operating-mode.html)。

配布gateは、外部Python/Gitをchild PATHから除外し、コピーした実行fileでusage/schema、init、doctor、fixture deliveryを確認することです。
現在のprocess timeoutはPOSIX向けです。Windows版はパッケージ化だけで対応完了にはなりません。
また、単体化しても対象プロジェクトのNode/Java/test runnerなどは、そのプロジェクト用に準備する必要があります。

文書を書くときは[ドキュメントの配置と網羅性](documentation-policy.md)を参照してください。領域・文書形式の選び方、漏れの点検、AI Agentの実行契約を定めています。

CLIだけで配置基準を読む場合は`harnessctl usage documentation`を実行し、JSONの`content`を読んでください。これは同梱の共通規約です。初期化後はrepositoryの配置規約と既存正本を先に確認し、同梱版で上書きしません。Agent向けの適用順序と既存文書が保持された場合の手順は`harnessctl usage agent`で取得できます。

文書作業を依頼する場合は「harness-documentを使い、既存正本を確認してから文書を更新してください」と伝えます。CLIからは`harnessctl usage harness-document`で手順を取得できます。
