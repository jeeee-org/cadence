# PROGRESS

## 現在地

**v0.3**。Claude Code / Codex両ホスト対応が完了し、運用フェーズ。共有flows/references/hookへホスト固有SKILLを重ね、Codexの`CADENCE`分類から`$cadence`へ接続済み。PJドメインフローは`.agents/cadence`を正本、`.claude/cadence`を後方互換とする。quorum後追いで判明したreadonly hookのblocking 3件は修正済み。

## 次にやること

1. Codexのreadonly hookを`/hooks`でtrustし、一時リポでdeny smoke testを行う（HANDOFF §4）
2. runbook↔alert対応表の改善後forward-testを、モデル容量回復後にfresh agentで再実走する
3. 実infra MCPを繋いだ両ホスト実走を行う（HANDOFF §4）
4. adversarialフィクスチャでreview/ABORTを発火し、gates/quorum経路も実地確認する

## 完了

- 2026-07-13: readonly hookのセンチネル自己解除・nested cwd誤判定・Codex trust案内を修正し、23件のAPI不要テストで固定 → [checkpoint](docs/checkpoints/2026-07-13.md)
- 2026-07-13: Codex版スキル・CADENCE連携・両環境install・共有フロー解決・apply_patch対応hook・15件のAPI不要テスト・実機forward-testを実装 → [checkpoint](docs/checkpoints/2026-07-13.md)
- 2026-07-06: 大規模改善8コミット（フィクスチャ実走13/13・validator・readonly hook・収束決定論化・PJローカルフロー・トリアージ）→ [checkpoint](docs/checkpoints/2026-07-06.md)

## ブロッカー

なし。改善後forward-testの再実走だけ、実行時のモデル容量不足で未完。

## 運用メモ

- 改善候補は`IMPROVEMENTS.md`、確定判断は`NOTES.md`、詳細はcheckpointへ記録する。
- read-only hookはopt-in。Codexではshell書込みの全経路を遮断しないため、MCP/資格情報/環境の物理境界を優先する。
