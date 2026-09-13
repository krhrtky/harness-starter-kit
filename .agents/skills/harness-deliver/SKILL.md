---
name: harness-deliver
description: 証拠とsemantic reviewが揃ったTaskのdelivery判定に使用する。
---

# Harness deliver

repository rootを作業基準とする。別ディレクトリからは `harnessctl --root <repo> ...` を使う。

`harnessctl check --phase delivery --task <path> --bundle <path> --findings <path> --ci`を実行する。
pass時だけdelivery可能と報告する。変更・検証範囲・残る運用条件を伝える。
このSkill自体はmerge、publish、deployを実行する権限を追加しない。実行はユーザーの依頼範囲に従う。
失敗はcode/pathごとに解消し、変更後はverifyとreviewを再生成する。
