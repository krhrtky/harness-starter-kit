# verification

test.unit capabilityはunittestでcontract/mutationを実行する。テスト対象と限界はvalidation文書を参照する。

[設計](../harness/design.md) / [CLI](../harness/cli.md) / [検証](../harness/validation.md)

検証機構を独自実装・tool・言語側へ分ける判断とresult受入は[検証guide](../harness/verification.md)、採用理由と反証は[ADR-003](../decisions/ADR-003-verification-delegation.md)に従う。

実行可能な外部toolと生成testの利用は[tool利用guide](../harness/verification-tools.md)を参照する。
