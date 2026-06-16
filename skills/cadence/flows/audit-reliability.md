# flow: audit-reliability

```yaml
purpose: >
  SRE 信頼性監査（read-only）。runbook / IaC / アラート・SLO 設定を列挙し、
  MCP 経由のライブ状態と突き合わせてドリフトを検出し、信頼性リスク
  （SPOF・単一障害ドメイン依存・アラート/SLO 欠落・runbook 乖離・容量/クォータ）を
  issue-ready なレポートにまとめる。何も変更しない。
mode: read-only
initial: plan
max_cycles: 3          # supervise ↔ review の上限。超えても改善なしなら ABORT（部分結果）
```

## steps

### plan
- **persona**: planner
- **tools**: Read, Glob, Grep, Bash(参照系), WebSearch, WebFetch
- **edit**: no
- **instruction**:
  - 信頼性サーフェスを列挙：runbook(`*.md`) / IaC(terraform・k8s マニフェスト) / アラート・SLO 設定 / オンコール・エスカレーション資料。
  - MCP で突き合わせるライブ信号を洗い出す（デプロイ状況・アラートルール・直近インシデント・リソースクォータ）。
  - 監査計画を出す：インベントリ＋各領域でチェックするリスク（SPOF・単一障害ドメイン・アラート/SLO 欠落/誤り・runbook 乖離・無制限リソース/クォータ余裕）。
- **next**:
  - サーフェス列挙とスコープが明確 → `audit`
  - 要件が不明・不足 → `ABORT`

### audit
- **persona**: sre-reviewer
- **tools**: Read, Glob, Grep, Bash(参照系), WebSearch, WebFetch
- **edit**: no
- **parallel**: 3        # 対象が多ければ最大3サブエージェントでスコープ分割（team_leader 相当）
- **mcp**: infra         # ライブ状態取得（参照系のみ）。実サーバ名・接続はユーザー環境で設定
- **instruction**:
  - 計画の各領域を1つずつ監査。runbook/IaC を **MCP のライブ状態と突き合わせドリフトを検出**。
  - 優先：SPOF・単一障害ドメイン依存／アラート・SLO の欠落・誤り／実態と合わない runbook 手順／無制限リソース／リトライストーム・thundering-herd。
  - 各 finding に：場所(file:line もしくは どの MCP 取得/コマンド)・故障シナリオ(トリガ＋制御点)・影響範囲(blast radius)・具体的修正案。
- **next**:
  - 監査完了 → `supervise`

### supervise
- **persona**: supervisor
- **tools**: Read, Glob, Grep, Bash(参照系)
- **edit**: no
- **judge(任意)**: 重要判断が割れる/確信が要る時は quorum に外注（材料を絞って渡す）
- **instruction**:
  - 監査の**完成度**（全領域被覆）と各 finding が **issue-ready**（具体シナリオ＋影響範囲＋修正案）かを検証。未被覆領域を特定。
- **next**:
  - 全領域を十分な品質で被覆し issue-ready → `COMPLETE`
  - 未被覆領域あり or 指摘が不十分 → `review`

### review
- **persona**: sre-reviewer
- **tools**: Read, Glob, Grep, Bash(参照系)
- **edit**: no
- **mcp**: infra
- **instruction**:
  - supervisor が指摘したギャップを再監査。read-only。audit と同じ finding フォーマット。
- **next**:
  - 再監査完了 → `supervise`

## convergence
`supervise ↔ review` を `max_cycles`(=3) まで回す。サイクルが上限に達しても改善が止まっている
（同じ指摘の往復・新規が増えない）なら **ABORT し、何が未被覆かを明記して部分結果を出す**。
「スコープが広がっている／改善が続く」間だけ継続する。

## gates（任意・決定論）
監査が定着し「毎回機械チェックしたい不変条件」が固まったら有効化する。
`references/gates.md` に従い Bash コマンドの exit code で機械判定する（非ゼロ→ `review`）。

```yaml
gates:
  - name: reliability-policy-check
    command: ./scripts/reliability-policy-check.sh   # 例：自作ポリシーチェック
    timeout_sec: 120
    on_fail: review
```
