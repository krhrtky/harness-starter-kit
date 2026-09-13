# Upgrade and migration policy

対象: 配布maintainerと導入repository owner。CLI versionはSemVer、レコードは整数schema_versionで管理する。
CLI v1はschema v1のみ通常操作可能。未知versionは早期失敗し、黙ってfieldを捨てない。

## Upgrade procedure

1. CLI wheelを固定versionで導入する。dependencyも導入先のlockfileで固定する。
2. `harnessctl migrate`でdry-runする。差分とconflictをレビューする。
3. Skills/schemaのローカル変更があれば、変更理由を保持して新distributionへ統合する。
4. `harnessctl migrate --apply`を実行する。更新前のfileは`.harness/backups/<timestamp>/`へ保存される。
5. `doctor`、fixture/contract test、導入先capabilityを実行する。新Taskでpreflight/evidenceを取り直す。

seed manifestの元hashに一致する未変更fileだけを自動更新する。project固有の文書・設定は上書きしない。
Skills/schemaの改変はconflictにする。同じschemaでも内容変更を検出するため、JSONの整形差分もconflictになり得る。
新seed fileは追加する。policy defaultの変更はproject設定へ自動適用せず、release差分をownerがレビューする。

## Supported migration

v0の`.harness/project.json`にある`baseline_mode`をv1の`mode`へ改名し、schema_versionを1へ更新する。
その他のfieldはv1と同じ契約を満たすこと。これはテスト済みの初期migrationであり、未定義の外部Harness形式を推測変換しない。
現在v1のprojectにはseed/Skills/schemaのmanifest差分を適用する。

## Rollback

apply結果のbackup pathから更新前fileを元pathへ復元する。dry-runのupdatesで新規追加されたfileは、レビューした一覧に従って除去する。
CLIも対応する前versionへ戻し、doctorを実行する。backupは既存fileのコピーであり、filesystem全体のtransactionではない。
apply中のI/O失敗では一部更新が残り得るため、CIでは使い捨てcheckout上で試してからレビューする。

## Breaking changes

新しいmajor/schema versionは、旧fixture、変換関数、dry-run、backup、移行後schema検査、READMEの手順を同じ変更に含める。
baselineを新規負債へ合わせて緩めるmigrationは認めない。例外が必要ならownerが根拠・期限・適用範囲を別decisionに定め、policy設計としてレビューする。
将来のsigned team bundlesや専用language adaptersは独立packageへ分離可能だが、Evidence Bundle契約を維持する。
