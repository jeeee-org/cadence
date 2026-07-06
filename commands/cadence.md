---
description: 構造化レビューループ（plan→audit→supervise→review）を宣言的フローで回す。read-only 監査・調査向け。フロー名と対象を指定（既定 audit-reliability）。
---

`cadence` スキル（`~/.claude/skills/cadence/SKILL.md`）を読み込み、その実行手順に従ってください。
引数の1語目が `flows/` にあるフロー名ならそれを、無ければ既定 `audit-reliability` を使い、
残りを対象スコープとする。曖昧なら確認する。実行ルール（read-only・収束・レポート様式）は
すべて SKILL.md が正であり、ここには書かない。

引数（フロー名＋対象スコープ）:
$ARGUMENTS
