# Validation and boundaries

`python -m unittest discover -s tests -v`はCLI end-to-end、JSON Schema、process adapter、baseline/ratchet、evolution、mutationを検査する。
テストは一時repositoryを使う。fixtureのsemantic passはテスト入力であり、人間/Agentのレビュー品質を証明しない。

| Mutation / contract | Expected result |
|---|---|
| Acceptance削除、未知field、未知schema version | invalid input |
| Architecture削除、domain欠損、knowledge変更 | blocker |
| MUSTからenforcement除去 | blocker |
| asset未検討、重複能力の再実装 | blocker |
| migration sourceへの配置、consumer欠落 | blocker |
| scope外の追加・削除 | verify前にblock |
| contract test失敗、timeout、実行file欠損 | passing evidenceを作らない |
| source更新、log改変、期限切れ、artifact使い回し | evidence gate失敗 |
| semantic view欠損、unknown、矛盾 | delivery失敗 |
| baselineへの新規負債追加、品質低下 | ratchet失敗 |
| team snapshot改変、policy緩和 | pin/control gate失敗 |
| traversal、root外symlink、shell metacharacter | path拒否 / literal argv |
| init再実行、既存AGENTS、変更済みSkill | 内容保存 / upgrade conflict |

## What is not proven

CLIは「新しい実装が別名の既存assetと意味的に同一か」「テスト集合が十分か」「quality採点が正しいか」を証明しない。
これらはstructured semantic findingとproject capabilityで補う。Code AST/依存graph/coverage/SAST等の専用adapterは同梱していない。
現時点の実行adapterはgeneric process、検出候補はPython/JavaScript/Go。その他の言語もargv登録で接続できる。
network team registry、署名、remote consumer CI、LLM reviewer自動起動、定期gardenのschedulerは提供しない。
team snapshot、reviewer、eval eventは監査可能な入力形式であり、外部identityや計測システムとの接続は拡張点。

## Distribution check

wheelを作り、別venvへinstallしてinitすることでschema/seed/Skillsが同梱されているか確認する。
追加のdiscovery契約は`tests/test_discovery.py`、単体binaryは`tooling/smoke_binary.py`で検証する。
全usage/schemaとinit後のfixture deliveryを外部Python/Gitなしで実行する。
ローカル実行環境はPython 3.11 / macOS arm64。process groupのtimeout実装はPOSIX向け。Windows native対応は未検証で、WSL/Linuxを使う。

## Skills source

10 Skillsは`.agents/skills/harness-*`へ配置する。`SKILL.md`のname/descriptionと必要時の本文読込みを前提にする。
形式は[OpenAIのSkillsドキュメント](https://learn.chatgpt.com/docs/build-skills)を参照した。
CLIの機械判定とsemantic reasoningを混在させず、Skills内でschema validatorを再実装しない。
