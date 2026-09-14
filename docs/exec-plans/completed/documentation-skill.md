# 文書Skillの同梱

Task: `.harness/tasks/documentation-skill.json`（DOCS-SKILL-1）。Owner: harness-maintainers。

## 配置と範囲

文書作業の共通入口を`harness-document`へ分離する。判断基準は既存の配置規約を正本とし、Skillには正本探索・配置判断・更新・確認の実行手順だけを置く。既存phase SkillsはTaskとscopeを引き継いで利用する。

`.agents/skills/harness-document/SKILL.md`がこのrepositoryでの利用先、`src/harnessctl/resources/skills/harness-document/SKILL.md`が配布元。既存のglobによるusage・init・migrate・wheel・binary同梱を再利用する。asset検索でharness.documentationの既存候補はなく、phase固有Skillへ単独文書作業を混在させないため新設する。

## 実行と証拠

- AC-SKILL: frontmatter検証、規約との意味レビュー、既存入口からの参照、配布元との一致を確認する。
- AC-DISTRIBUTION: usageで全文取得、initで配置、migrateで追加、ローカル編集時のconflictと保存をテストする。wheelを生成して内容を照合し、ホスト向けbinaryをbuildして外部Python/Gitなしのsmokeを実行する。
- test.unitをEvidenceとして記録し、各ACとglobal-impactを3視点でレビューしてdeliveryを照合する。配布物の検証ログもreviewの根拠へ含める。

## 影響と戻し方

登録consumerとactive migrationはない。schema・policy・capability・quality採点を変えない。既存の10 Skillsを削除せず1件追加する。配布試験は固定件数だけでなくusageの列挙と配置されたSkillを照合する。

問題時は今回のSkill・参照・検証変更を戻し、前のTaskの文書配置規約とCLI導線を保持する。公開済み配布物を差し替える操作は行わない。生成するbinaryは実行ホスト向けであり、他OS/CPUの検証は各release runnerで行う。
