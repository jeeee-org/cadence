# flow: fix-reliability

```yaml
purpose: >
  信頼性 issue の修正（mode: edit・有人）。audit-reliability の指摘（または個別 issue）を入力に、
  最小の安全な変更を立案 → 人の承認 → 適用（IaC/runbook/設定ファイル）→ 決定論ゲートで検証 →
  read-only 再レビュー で詰める。各変更は人が承認してから適用する（無人で勝手に大改修しない）。
mode: edit
initial: plan
max_cycles: 3
require_human_approval: true   # 変更適用の前(propose)と COMPLETE の前(supervise)に人の承認を取る
```

## input
- `audit-reliability` のレポート（`.cadence/runs/<id>/02-audit-reliability.md`）か、個別 issue の記述。
- 対象を **1件（or 少数）に絞る**。巨大な一括改修にしない（有人前提・小さく直す）。

## steps

### plan
- **persona**: sre-fixer
- **edit**: no
- **instruction**:
  - 入力の指摘を1件ずつ受け、**最小の安全な変更**を設計：何を・なぜ・影響範囲・**ロールバック手順**。
  - 大きすぎる/曖昧な指摘は分割するか、人に差し戻す。
- **next**:
  - 計画が明確 → `propose`
  - 要件が不明・対象が大きすぎ → `ABORT`（人に差し戻し）

### propose
- **persona**: sre-fixer
- **edit**: no
- **human_approval**: required        # ここで止まって人に提示し承認を待つ（SKILL.md「編集モードと人の承認」）
- **instruction**:
  - 具体的な変更内容（**差分プレビュー or 変更計画**）＋影響範囲＋ロールバックを人に提示し、**承認を得る**。
  - 承認されるまで一切適用しない。修正要望があれば `plan` に戻す。
- **next**:
  - 承認 → `implement`
  - 修正要望 → `plan`
  - 却下 → `ABORT`

### implement
- **persona**: sre-fixer
- **edit**: yes
- **instruction**:
  - 承認された変更**だけ**を**リポのファイル（IaC / runbook / 設定）に**ホストで利用可能な編集手段で適用。スコープ外は触らない（scope creep 禁止）。
  - ⚠️ **ライブ本番への適用（`terraform apply` 等のミューテーション）は cadence では行わない**——通常の人が回す変更/デプロイプロセスに委ねる。cadence は source of truth を直すところまで。
  - （opt-in）どうしても MCP の書き込みで適用したい場合のみ、`propose` の承認にその適用も明示的に含めること。既定では行わない。
- **next**:
  - 適用完了 → `verify`

### verify
- **persona**: sre-fixer
- **edit**: no
- **gates**: 決定論ゲートで機械検証（`references/gates.md`）
- **instruction**:
  - テスト / validate / policy-check を実行し exit code で判定。出力を `NN-gate-*.md` に残す。
- **next**:
  - ゲート合格 → `review`
  - ゲート不合格 → `implement`（直す）

### review
- **persona**: sre-reviewer
- **edit**: no
- **mcp**: infra                       # read-only。修正後の状態を再確認（資格情報も read-only）
- **instruction**:
  - 修正が**正しく・新たな信頼性リスクを生んでいない**かを read-only で確認（監査と同じ視点）。スコープ逸脱もチェック。
- **next**:
  - 問題なし → `supervise`
  - 問題あり → `implement`

### supervise
- **persona**: supervisor
- **edit**: no
- **human_approval**: required        # COMPLETE の前に人の最終承認
- **instruction**:
  - 対象 issue が解決し検証も通ったか、issue-ready に閉じたかを判定。**COMPLETE の前に人の最終サインオフ**を取る。
- **next**:
  - 解決＆承認 → `COMPLETE`
  - 未解決 → `review`
  - 収束しない → `ABORT`

## convergence
`max_cycles`(=3) は `implement ↔ verify ↔ review` の**ハードキャップ**：state.md のサイクル数が上限に
達したら必ず停止し、**ABORT として適用済みの変更とロールバック手順を明記**して人に返す。上限前でも
同じゲート失敗・同じ指摘の繰り返し（直すたび別の問題が出る等）は停滞として早期 `ABORT`。

## gates（決定論・verify で使用）
```yaml
gates:
  - name: reliability-verify
    command: ./scripts/reliability-verify.sh   # 例：テスト＋terraform validate＋policy-check
    timeout_sec: 300
    on_fail: implement
```
