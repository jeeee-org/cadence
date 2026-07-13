# flow: optimize-context

```yaml
purpose: >
  Claude Code / Codex プロジェクトのコンテキスト/指示サーフェス（グローバル＋プロジェクトの
  CLAUDE.md / AGENTS.md、
  スキルの description、PROGRESS/NOTES、memory 残骸、常時ロードされる参照）が肥大して指示追従の
  精度が落ちている状態を、ルールを失わずにスリム化・最適化する（mode: edit・有人承認）。
  冗長/重複/矛盾/陳腐を除き、時系列の詳細は checkpoint へ退避し、毎ターン・ロードのトークンを減らす。
  各変更は人が承認してから適用する（cut bytes, not meaning）。
mode: edit
initial: plan
max_cycles: 3
require_human_approval: true   # 適用前(propose)と COMPLETE 前(supervise)に人の承認を取る
```

## input
- 対象プロジェクト（ディレクトリ）。任意で「特に重い/怪しいファイル」の指定。
- **触ってよい範囲を確認**：プロジェクト内ファイルのみか、ホストのグローバル設定（`~/.claude/` / `${CODEX_HOME:-~/.codex}/` / `~/.agents/skills/`。全PJに影響・版管理外のことが多い＝戻しにくい）も対象に含めるか。

## steps

### plan
- **persona**: planner
- **tools**: Read, Glob, Grep, Bash(参照系)
- **edit**: no
- **instruction**:
  - コンテキスト・サーフェスを列挙し、**常時ロード**（毎ターン/セッション開始）と**オンデマンド**を区別：
    - 常時：ホストのグローバル指示、プロジェクト `CLAUDE.md` / `AGENTS.md`、各スキルの `description`/frontmatter、システムリマインダ（memory 残骸含む）、セッション開始時の `PROGRESS.md`。
    - オンデマンド：スキル本体・`references/`・`docs/*`・`docs/checkpoints/`（普段ロードされない）。
  - 規模を測る（`wc -l`／概算トークン）。**常時ロード × 大きい**ものを最優先対象に。
  - 既知の肥大アンチパターンに当たりをつける：global↔project指示の重複／CLAUDE.md・AGENTS.mdに積もったセッション履歴／肥大したPROGRESS（完了項目をcheckpointへ退避すべき）／矛盾する指示／陳腐化した記述／memory残骸。
  - 触れる範囲（project のみ / global 含む）を確定する。
- **next**:
  - サーフェスと優先対象が切れた → `audit`
  - 範囲・対象が曖昧 → `ABORT`（何を決めればよいか明示）

### audit
- **persona**: context-optimizer
- **tools**: Read, Glob, Grep, Bash(参照系)
- **edit**: no
- **parallel**: 3        # ファイル/領域が多ければ分担（各サブエージェントにも read-only と出力様式を明示）
- **instruction**:
  - 優先対象を精査し、**削減候補を分類して列挙**。各候補に：〔場所(file:line)〕〔種別：重複/矛盾/陳腐/誤配置/冗長〕〔常時ロードか〕〔提案：削除/統合(→どこ)/移設(→checkpoint・NOTES・reference)/言い換え〕〔常時ロード削減見込み（行/概算トークン）〕〔**失われるルールは無いか**（あるなら明示）〕。
  - **ルール保全が最優先**：重複は「同じ規則が他にある」ことを*確認してから*、陳腐は事実を*確認してから*候補化（推測で削らない）。
  - 削減効果（常時ロードのバイト減）が大きい順に並べる。
- **next**:
  - 削減候補が出揃った → `propose`

### propose
- **persona**: context-optimizer
- **edit**: no
- **human_approval**: required        # ここで止まって人に提示し承認を待つ（SKILL.md「編集モードと人の承認」）
- **instruction**:
  - 人に提示する：①**差分プレビュー**（or 変更計画）②**ルール対応表**（元の各ルール → 残す/統合(→先)/移設(→先)/意図的に削除(要承認)）③常時ロード削減見込み。
  - ⚠️ **グローバル設定への変更は別枠で明示**（全PJに影響・版管理外＝戻しにくい）。事前バックアップを提案してから承認を取る。
  - 承認を得るまで一切適用しない。修正要望があれば `audit`/`plan` に戻す。
- **next**:
  - 承認 → `apply`
  - 修正要望 → `audit`
  - 却下 → `ABORT`

### apply
- **persona**: context-optimizer
- **edit**: yes
- **instruction**:
  - 承認された変更**だけ**をホストで利用可能な編集手段で適用。スコープ外は触らない（scope creep 禁止）。
  - **移設は「先に退避先へ書いてから元を削る」**（情報を一瞬でも失わない）。
  - global を含む承認だった場合のみ global を編集（提案したバックアップを先に取る）。
- **next**:
  - 適用完了 → `verify`

### verify
- **persona**: context-optimizer
- **edit**: no
- **gates**: 決定論ゲートで機械検証（`references/gates.md`）
- **instruction**:
  - リンク整合（dangling な `[[wiki link]]`／壊れた相対リンクが無い）・必須セクションの存在・ファイルがパースできる、等を機械チェック。出力を `NN-gate-*.md` に残す。
  - 移設先に内容が実在することも確認（「消えただけ」を検出）。
- **next**:
  - ゲート合格 → `supervise`
  - 不合格 → `apply`（直す）

### supervise
- **persona**: supervisor
- **edit**: no
- **human_approval**: required        # COMPLETE の前に人の最終サインオフ
- **judge(任意)**: 削除の是非が**割れる/重要**な時は quorum に外注（対応表と該当箇所を絞って渡す）。
- **instruction**:
  - **ルール対応表で全ルールが追えるか**（落ちていないか）、矛盾が解消したか、常時ロードのトークン削減が達成されたかを判定。COMPLETE の前に**人の最終承認**を取る。
- **next**:
  - 達成＆承認 → `COMPLETE`
  - ルール欠落の疑い/不足 → `audit`
  - 収束しない → `ABORT`（適用済みと未処理を明記して返す）

## convergence
`max_cycles`(=3) は `apply ↔ verify ↔ audit` の**ハードキャップ**：state.md のサイクル数が上限に達したら
必ず停止し、**ABORT として適用済みの変更と未処理候補・（global を触ったなら）バックアップ位置を明記**して
人に返す。上限前でも削減候補 ID 集合に差分が無い（削っては別の重複が出る等の堂々巡り）なら早期 `ABORT`。

## gates（決定論・verify で使用）
```yaml
gates:
  - name: link-and-structure-check
    command: <リンク整合＋必須見出しチェックのコマンド>   # 例：dangling [[link]] 0 / 相対リンク到達性 / 必須セクション存在
    timeout_sec: 120
    on_fail: apply
```

> 安全網（mode: edit・有人）：適用前の承認＋ルール対応表＋決定論リンクチェック＋最終サインオフ。
> 特に **ホストのグローバル設定は版管理外で戻しにくい**ため、編集は別承認＋バックアップを徹底する。
