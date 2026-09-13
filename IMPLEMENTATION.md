# Implementation status

Release: 1.0.0。検証日: 2026-09-14。環境: macOS / Python 3.11.3。

## Implemented requirements

| 要求 | 実装 |
|---|---|
| machine-readable control plane / schema | `.harness/`、Draft 2020-12の18 schema、CLI同梱schemaとの照合 |
| knowledge structure | `docs/`の27 interface index、architecture、plans、decisions、quality、evolution |
| root AGENTS router | `AGENTS.md`、非破壊init、既存routerをpreservedとして報告 |
| 14必須command | init / inspect / doctor / inventory / preflight / check / verify / evidence / knowledge / quality / feedback / promote / baseline / migrate |
| capability / adapter | enabled registry、Adapter protocol、generic process、Python/JS/Goの検出候補 |
| 主要data contracts | Task、Evidence、semantic finding、asset、quality、current/target/transition |
| Codex Skills | bootstrap / intake / preflight / plan / verify / review / deliver / learn / garden / adapt |
| greenfield / brownfield | UNKNOWN、該当interfaceのreadiness、既存欠損baseline、単調ratchet |
| fixtures / mutation / contract test | 11 repository scenario、48 unittest、CLIのdelivery end-to-end |
| provider-independent CI | JSON + exit status、`check --ci`、`verify --ci`、`tooling/ci.py` |
| distribution / migration | wheel同梱、seed manifest差分、conflict、dry-run、backup、v0→v1 migration |
| Repository Evolution | knowledge鮮度、quality非劣化、重複候補、feedback/promotion、asset lifecycle |
| Team Evolution | pin済みteam snapshot、加算policy、shared catalog、consumer確認、eval集計 |

## Gate behavior

preflight receiptはTask、source file map、control plane、quality、asset catalogを結び付ける。
deliveryでは実際の追加・更新・削除を検査し、scope逸脱、未計画の配置、migration source、未検討asset、未登録/不一致asset、quality低下をblockする。
Evidenceはcapability・終了値・log/artifact hash・時刻・source digestを照合する。
semantic reviewは各ACとglobal-impactについて3視点を要求し、欠損・unknown・fail・矛盾をblockする。

## Verification results

- ソース環境: 48 tests passed。11 fixture scenarioをmatrix内で実行。
- 初期wheelの別venv検証: 43 tests passed。追加したdiscoveryはソーステストと単体binaryのsmoke testで検証。
- wheelからのinit: 18 schemas、10 Skills、50 seed filesを同梱確認。
- Starter Kit自身の`doctor` / `check --ci`: pass。
- 10 Skills: skill-creatorのquick_validateで全件pass。
- v1 migration dry-run: updatesなし、conflictsなし。

## Binary distribution and offline discovery

- `usage`で目次、guide、実parserの引数、10 Skillsをrepository初期化前に取得。
- `schema`で18契約を取得。runtimeと同じversionの文書をオフラインで参照。
- macOS arm64単体binaryをローカルでbuildし、外部Python/Gitなしでfixture deliveryまでpass。
- GitHub workflowはmacOS/Linux × arm64/x86_64を検証してtag Releaseへ配布。
- archiveにSTART-HERE.md、第三者license、SHA-256を同梱/添付。
- macOS Developer ID署名・notarizationは未接続。

## 未実装・未検証の接続先

- 専用のAST解析、coverage、SAST、browser、各言語framework adapter。現在はgeneric processで接続する。
- remote team registryの同期・署名・identity認証。現在はレビュー対象のローカルpin済みsnapshotを扱う。
- production deploy、remote consumer CI、自動garden scheduler。provider-independent commandを外部基盤から呼ぶ。
- LLM reviewerの自動起動とSkillsの実LLM性能eval。入力schemaとeval registryは実装済み。
- Windows native。process group timeoutはPOSIXで検証済み。

ドメイン仕様、SLO、target architecture、検証command、quality基準は導入先の責務。
CLIは意味論の真偽や本人承認を証明しない。詳細は[design](docs/harness/design.md)と[validation](docs/harness/validation.md)。
