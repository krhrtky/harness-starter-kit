# GitHub binary distribution

配布先: `krhrtky/harness-starter-kit`。初期公開範囲はprivate。
ブラウザからGitHubのReleasesを開き、OS/CPUが一致するarchiveと`.sha256`を取得する。
private repositoryの取得にはGitHubへの認証とrepositoryアクセス権が必要。

macOSは`shasum -a 256 -c <archive>.sha256`、Linuxは`sha256sum -c <archive>.sha256`で確認する。
archiveを展開し、START-HERE.mdを読む。`./harnessctl usage`がオフラインで使える。

## Discovery contract

| 入口 | 取得する内容 | repository |
|---|---|---|
| `--help` | usageへの入口とcommand一覧 | 不要 |
| `usage` | version付き目次 | 不要 |
| `usage commands` | 実際のparserから引数・choices・必須flag | 不要 |
| `usage agent` | Agentの開始・完了・upgrade手順 | 不要 |
| `usage harness-intake`など | 同梱Skill全文 | 不要 |
| `schema` / `schema task` | 契約一覧 / schema本文 | 不要 |
| `init`後のAGENTS/docs/Skills | project内からの参照とSkill発見 | 必要 |

binaryにPython runtimeだけでなくusage・schema・seed・Skillsを同梱する。
同梱文書の取得にGitHubアクセスやソースcheckoutを必要としない。
CLI操作はbinaryのversion、ドメイン判断はrepositoryのknowledgeを根拠にする。

## Maintainer workflow

`.github/workflows/release.yml`がmain/PRで4対象のbuildとsmoke testを実行する。
versionと一致する`v*` tagをpushすると、全対象の成功後にReleasesへarchiveとchecksumを登録する。
Actionsはcommit SHA固定。対象runnerはUbuntu 22.04 x86_64/arm64、macOS 14 arm64、macOS 15 Intel。
release先URLをworkflowへ埋め込まず、実行repositoryを使う。

```sh
python -m pip install . -r requirements-build.txt
python tooling/build_binary.py --output dist/bin --work build/pyinstaller
python tooling/smoke_binary.py dist/bin/harnessctl
python tooling/package_release.py dist/bin/harnessctl --output dist/release
```

smoke testは実行fileだけを別ディレクトリへコピーし、child PATHからPython/Gitを除く。
全usage/schemaの読取り、initによるSkills展開、fixtureのpreflight→verify→deliveryを確認する。
fixtureのsemantic findingはテスト入力であり、実プロジェクトのレビューを代替しない。

macOSのDeveloper ID署名・notarizationは未接続。外部利用者向けの一般配布前に署名・公証を整備する。
PyInstallerのonefileは起動時に一時領域へ展開するため、read-only/noexec環境では実行条件の確認が必要。

実装根拠: [PyInstaller](https://pyinstaller.org/en/stable/usage.html)、[GitHub runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)。
