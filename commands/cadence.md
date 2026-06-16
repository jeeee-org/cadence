---
description: 構造化レビューループ（plan→audit→supervise→review）を宣言的フローで回す。read-only 監査・調査向け。フロー名と対象を指定（既定 audit-reliability）。
---

`cadence` スキルを使って、構造化レビューループ（plan → audit → supervise → review）を実行してください。

手順:
1. 引数から **フロー名**（既定 `audit-reliability`）と **対象スコープ**（ディレクトリ/サービス/runbook 等）を取り出す。曖昧なら確認する。
2. `~/.claude/skills/cadence/SKILL.md` の実行手順に従い、`~/.claude/skills/cadence/flows/<flow>.md` を読み込んでステートマシンを回す。
3. ペルソナは `~/.claude/skills/cadence/references/personas/<persona>.md`、決定論ゲートは `~/.claude/skills/cadence/references/gates.md` を参照する。
4. `mode: read-only` のフローでは **Edit/Write/破壊的 Bash を使わない**（指摘・リスク・修正案のみ）。MCP は参照系のみ。
5. `max_cycles` を守り、収束しないなら **ABORT して部分結果を率直に報告**する。高ステークスの判断が要る step は `quorum` に外注してよい。
6. 最後に **issue-ready な最終レポート**（場所／故障シナリオ／影響範囲／修正案）＋監査証跡を出す。

引数（フロー名＋対象スコープ）:
$ARGUMENTS
