---
name: cadence
description: 完成条件が明確な被覆型の監査・調査・定型修正を、宣言的フローの plan → audit → supervise → review で反復し、証跡と収束判定を残して実行する。ユーザーが「cadenceで」「$cadence」と明示した時、またはclaude-rulesのトリアージでCADENCEとなり実行も求められた時に使う。audit-reliability、error-analysis、investigate-subsystem、optimize-context、fix-reliabilityとPJ固有フローに対応する。T0の単純作業、T1の広さ型高ステークス判断、T2aの深さ型単独検証には使わない。
---

# Cadence for Codex

メインCodexをステートマシンとして使い、フロー定義とペルソナに従って各stepを実行する。`SKILL_DIR` はこの `SKILL.md` があるディレクトリとして解決し、CWDや `~/.claude` に依存しない。

## 1. フローと対象を確定する

1. ユーザー指定のフローを優先する。未指定なら依頼内容から次を選ぶ。
   - 信頼性監査: `audit-reliability`
   - 障害・エラー原因分析: `error-analysis`
   - サブシステム理解: `investigate-subsystem`
   - 指示コンテキスト最適化: `optimize-context`
   - 信頼性指摘の修正: `fix-reliability`
2. `<flow>.md` を次の順に探す。同名は上位を使う。
   1. `<対象PJ>/.agents/cadence/flows/<flow>.md`
   2. `<対象PJ>/.claude/cadence/flows/<flow>.md`（後方互換）
   3. `$SKILL_DIR/flows/<flow>.md`
3. `mode`、`initial`、`max_cycles`、steps、gates、有人承認点を読む。対象スコープが実行結果を変えるほど曖昧なら確認する。
4. PJ固有フローを作る時だけ `references/flow-authoring.md` を全文読む。

## 2. ラン状態を作る

- 対象PJのルートで `.cadence/runs/<run-id>/` を作り、各stepを `NN-<step>.md`、並列結果を `NN-<step>-<agent>.md` に保存する。
- `.cadence/runs/<run-id>/state.md` を正とし、現在step、supervise通過回数、遷移履歴と理由、finding ID集合、gate結果を遷移ごとに更新する。
- `mode: read-only` ならエンジンのshell制御操作で `.cadence/readonly` を作る。structured `apply_patch`では変更しない。COMPLETE / ABORTのどちらでも、最終成果物とstate確定後にshell制御操作で削除する。
- 対象リポの実ファイルはread-onlyフローで変更しない。`.cadence/` の証跡だけを書いてよい。

## 3. stepを実行する

- personaを次の順に読み、その役割・禁止事項・出力様式を守る。
  1. `<対象PJ>/.agents/cadence/personas/<persona>.md`
  2. `<対象PJ>/.claude/cadence/personas/<persona>.md`
  3. `$SKILL_DIR/references/personas/<persona>.md`
- フローのツール名を能力ラベルとして扱い、現在のCodexで使える対応能力へ写像する。
  - `Read` / `Glob` / `Grep`: ローカル読取・検索。検索は原則 `rg` / `rg --files`。
  - `Bash`: shell実行。read-only stepでは参照・検査コマンドだけを使う。
  - `WebSearch` / `WebFetch`: web検索・取得。必要な時だけ使い、出典を残す。
  - `Edit` / `Write`: `apply_patch` など現在利用可能な編集手段。`edit: yes` かつ承認済みの場合だけ使う。
  - `Task`: Codexの直接サブエージェント。
- `parallel: N` があるstepだけ、利用可能スロットの範囲で最大N体の直接サブエージェントへ重複しないスコープを割り当てる。子に再委譲させず、read-only制約とfinding様式を明示する。メインが結果を検証・統合して証跡へ書く。
- `mcp: <server>` がある時は利用可能な対応MCPを探し、参照系ツールだけを使う。サーバが無い時は推測で埋めず、未被覆として記録する。
- findingは安定IDを使い、`references/report-template.md` の ID / 場所 / 故障シナリオ / 影響範囲 / 修正案を揃える。

## 4. 安全境界を守る

- read-onlyでは `apply_patch`、書込みshell、破壊的コマンド、書込みMCPを対象ファイルへ使わない。
- 物理境界は、参照専用MCP、read-only資格情報、書込み不能な環境の順で優先する。opt-inの `hooks/readonly-guard.py` はローカル編集を補助するが、全shell経路を遮断する境界とはみなさない。
- `mode: edit` では `human_approval: required` のstepで、差分案・影響・ロールバックを提示して明示承認を待つ。承認範囲だけを最小・可逆に編集する。本番適用は明示的に承認範囲へ含まれない限り行わない。

## 5. 遷移と収束を判定する

- step出力を保存してからフローの `next` 条件で遷移する。
- supervise通過回数が `max_cycles` に達したら必ず停止する。被覆十分ならCOMPLETE、不足ならABORTで部分結果を返す。延長しない。
- 上限前でも、前サイクルからfinding IDが増えず、既存findingもissue-readyへ改善していなければ停滞としてABORTする。
- gatesがあれば `references/gates.md` を読み、指定コマンドのexit codeで判定する。stdout/stderrとexit codeを証跡へ残し、非ゼロなら `on_fail` へ遷移する。
- 判断が高ステークスで割れる時だけ、利用可能な `$quorum` に絞った判断材料を渡して裏取りする。fan-out前に追加コストとレイテンシを宣言する。

## 6. 完了する

- 全stepを `references/report-template.md` に沿って融合し、被覆済み/未被覆、遷移要約、gate結果、read-only確認方法を添える。
- ABORTでも部分finding、停止理由、再開に必要な条件を返す。
- `state.md` の最終状態をCOMPLETEまたはABORTへ更新してから、shell制御操作で `.cadence/readonly` を削除する。structured `apply_patch`でセンチネルを変更しない。

## 改善記録

汎用ハーネスとして再利用できる新しい弱点だけ、そのターン中に `$SKILL_DIR/IMPROVEMENTS.md` の既存項目へ統合する。タスク固有の進捗やPJ固有ドメイン知識は書かない。
