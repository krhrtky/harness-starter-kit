---
name: harness-verify
description: 実装済みTaskの検証とEvidence Bundle生成に使用する。
---

# Harness verify

repository rootを作業基準とする。別ディレクトリからは `harnessctl --root <repo> ...` を使う。

`harnessctl verify --task <path>`でregistryの検証を実行し、返されたbundle pathを保持する。
失敗時はlogとartifactを読み、Task scope内で修正し再実行する。成功出力を捏造・編集しない。
`harnessctl evidence validate --task <path> --bundle <path>`で鮮度と整合を再検査する。
ログに秘密情報を含む場合は共有前に実行環境を修正し再生成する。既存bundleのlog改変はintegrity gateを壊す。
