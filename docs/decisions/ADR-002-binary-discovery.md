# ADR-002: バイナリにusageと入力契約を同梱する

Date: 2026-09-14。Status: Accepted。Owner: harness-maintainers。

## Context

GitHubから実行fileだけを取得するAgentは、ソースrepositoryのREADMEやSkillsを参照できるとは限らない。
runtimeだけを配布すると、CLIの使い方とTask入力契約を発見できない。

## Decision

macOS/Linux向けPython同梱バイナリとSTART-HERE.mdをGitHub Releasesで配布する。
CLI自身がusageの目次・実際の引数・guide・Skill全文・schemaをオフラインで返す。
init後には同梱文書とSkillsをrepositoryへ展開し、AGENTS routerに入口を置く。

## Alternatives

| Option | Benefit | Cost |
|---|---|---|
| バイナリ同梱usage（採用） | offlineで実行versionと一致する手順を取得 | 配布前にresource同梱を検証する必要 |
| GitHub READMEへのURLだけ | 配布物が小さい | network/認証と文書versionに依存 |
| 全手順を--helpに記載 | 単一入口 | 長文で発見しにくく、schemaやSkillの段階取得ができない |
| Go/Rustへ書換え | native CLIとして配布可能 | runtime変更ではusage消失問題は解消せず、既存gateの再実装が必要 |

## Consequences

Agentは`usage`→topic→schemaと段階的に必要情報だけを読む。ソースcheckoutは不要。
実装言語をPythonのまま維持し、既存contract testsを再利用する。
配布側はOS/CPU別buildを実施し、実行fileだけのsmoke testをrelease gateにする。
macOS署名・notarization、Windows対応は別の配布拡張。現行版はmacOS ad-hoc署名。

## Validation and review

外部Python/GitをPATHから除外した子プロセスで、全usage topic/schema、init、fixture deliveryを検証する。
配布先はkrhrtky/harness-starter-kit、初期visibilityはprivate。公開範囲を変える場合はownerが決定する。
見直し条件: public配布、Windows需要、起動時間またはサイズの運用上の問題。
[ADR-001](ADR-001-distribution.md)、[Release手順](../harness/releases.md)。
