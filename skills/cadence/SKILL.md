---
name: cadence
description: 構造化レビューループ（plan → audit → supervise → review）で、読み取り専用の監査・調査タスクを宣言的フローとして回す自作ハーネス。フロー定義(flows/*.md)とペルソナ(references/personas/*.md)を読み込み、メインの Opus 4.8 がステートマシンとして実行する。収束/打ち切りを監視し、決定論ゲート(Bash)と高ステークス判断の quorum 外注を組み込める。SRE 的な「巨大MD＋ライブ状態の欠陥発見→検証」に向く。単純な一問一答には使わない。
---

# Cadence（plan → audit → supervise → review ハーネス）

複数 step の**構造化レビューループ**を宣言的フローとして回すハーネス。
TAKT の思想（AI の自律に委ねず外側から構造で律する）を Claude Code スキルとして自作・再実装したもので、
**TAKT には依存しない**（概念の参考のみ）。**メインの Opus 4.8 セッションがエンジン**＝フローを読み、各 step をペルソナとして実行し、遷移を判定する。

> 関連スキル：高ステークスの**判断**を多モデルで突き合わせたい step は [quorum] に外注できる（§5）。
> cadence＝「手順を回す指揮者」、quorum＝「重要判断の専門家会議」。
>
> **ファイルの場所**：既定のインストール先は `~/.claude/skills/cadence/`。
> 以下の `flows/...` `references/...` は同配下を指す（CWD 非依存の絶対パスで読む）。

## 何をするスキルか / いつ使うか
- **使う**：複数 step の監査・調査を**反復ループで詰める**タスク。特に SRE 的な「巨大MD（runbook/IaC/設定）＋ライブ状態の欠陥発見→検証」。read-only 既定。
- **使わない**：単純な一問一答、1ショットで終わる作業。ループのオーバーヘッドが見合わない。

## 実行手順（メイン Opus がエンジンとして回す）

### 0. フローと対象を決める
- ユーザー指定のフロー名（既定 `audit-reliability`）の定義を `~/.claude/skills/cadence/flows/<flow>.md` から読む。
- フローの `mode`（`read-only` | `edit`）・`initial`・`max_cycles`・各 step（persona / tools / parallel / mcp / instruction / 遷移）を把握する。
- 監査/調査の**対象スコープ**（どのディレクトリ・どの runbook・どのサービス）をユーザーから受け取る。曖昧なら確認する。

### 1. ランの作業領域を用意（成果物の追跡可能性）
- `./.cadence/runs/<run-id>/` を作る（`<run-id>` は短い識別子。日付＋連番など）。各 step の出力を `NN-<step>.md` として残す（TAKT の `.takt/runs/` に相当する監査証跡）。
- `.cadence/` は対象リポの `.gitignore` に入れておくとよい（成果物であって追跡対象ではない）。

### 2. ステートマシンを回す
`initial` step から開始し、各 step を以下の規約で実行して遷移する：

- **ペルソナを着る**：step の `persona` を `references/personas/<persona>.md` から読み、その役割・価値観・禁止事項に従って step を遂行する。
- **read-only の徹底**（`mode: read-only` または step `edit: no`）：**`Edit`/`Write`/破壊的 Bash を使わない**。閲覧は `Read`/`Glob`/`Grep`/参照系 Bash／MCP のみ。書き換え・適用は行わない（指摘とリスクと修正案を出すだけ）。
  - ⚠️ メインセッションは Edit/Write 権限を持つため、read-only は**運用規律で担保**する（この制約を毎 step 自己点検する）。
- **並列 step（`parallel: N`）**：対象が多い時は `Task` で**最大 N 個のサブエージェント**を起動し、スコープを分割して並列監査させる（TAKT の team_leader 相当）。各サブエージェントにも read-only と出力フォーマットを明示する。
- **ライブ状態（`mcp: <server>`）**：step が MCP 指定を持つなら、その MCP ツールでライブ状態を取得し、ドキュメント（runbook/IaC）と**突き合わせてドリフトを検出**する。MCP は**参照系のみ**使う（ライブ環境を変更しない）。
- 各 step の結論を `NN-<step>.md` に書き、次 step に必要な要約だけを渡す（コンテキスト肥大を避ける）。

### 3. supervise（収束判定）と遷移
- `supervise` step では、それまでの監査が**完成度十分か**（全スコープ被覆・各指摘が issue-ready＝具体シナリオ＋影響範囲＋修正案）を判定し、フロー定義の遷移ルールに従って `COMPLETE` / `review` / `ABORT` を選ぶ。
- **収束監視（loop monitor）**：`supervise ↔ review` のサイクルが `max_cycles` を超えても改善が止まっている（同じ指摘の往復・新規が増えない）なら **`ABORT` し、部分結果を率直に報告**する（無限ループにしない）。「広がっている／改善が続く」間だけ回す。

### 4. 決定論ゲート（任意・`gates`）
- フロー/step に `gates`（Bash コマンド）があれば、`references/gates.md` に従い**コマンドを実行して exit code で機械判定**する（テスト/lint/ポリシーチェック）。
- 非ゼロ＝不合格 → フロー定義の遷移（多くは `review` に戻す）。LLM 判定ではなく**決定論**で弾く層（モデルのブレを吸収する核）。

### 5. 高ステークス判断は quorum に外注（任意・合成）
- supervise や、判断が割れる重要 step で**確信が要る**時は、判断材料を絞って [quorum] に渡し、多モデルの合意/矛盾/盲点で裏取りする。
  - 渡す前の「材料を絞って自己完結プロンプトにする」手順は quorum 側 `references/context-packing.md`（司書手順）に従う。
- quorum は cadence の中で**普通のスキル呼び出し**として使える（スキルはセッションをロックしない）。コスト N 倍なので**ここぞの判断**に限定する。

### 6. fuse（最終レポート）
- 全 step の結論を統合し、**issue-ready な最終レポート**を出す：各 findings に〔場所(file:line / どの MCP 取得)〕〔故障シナリオ：トリガ＋制御点〕〔影響範囲(blast radius)〕〔修正案〕。
- 末尾に**監査証跡**（どの step で何を判定したか・ABORT したなら何が未被覆か・ゲート結果）を畳んで添える。

## フロー定義の書式（`flows/*.md`）
各フローは「purpose / mode / initial / max_cycles / steps（persona・tools・parallel・mcp・instruction・遷移）/ convergence / gates(任意)」を持つ。新しい監査・調査タイプを足したい時は、この書式の `flows/<name>.md` を1枚足すだけ（SKILL.md は無改修）。同梱例：`flows/audit-reliability.md`（SRE read-only 信頼性監査）。

## 注意・限界
- **read-only はメイン権限では運用規律依存**（Edit/Write を持つため）。ライブに触る MCP は参照系のみに絞ること。
- レイテンシ・コストはループ回数×step に比例。`max_cycles` を必ず設定し、収束しないなら部分結果で打ち切る。
- ペルソナ/フローは**テキスト指示**であり実行系の強制ではない。守られているかは step ごとに自己点検する。
- quorum 外注は**判断（推論）の冗長化**であって作業の冗長化ではない。日常の作業劣化はゲート＋リトライで吸収する。
