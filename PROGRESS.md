# PROGRESS — cadence

## 現在地
**v0.2**。構造完成＋合成フィクスチャで実走検証済み＋「共通エンジン（このリポ・public）／ドメインフローは各PJ側」の分離まで実装済み。トリアージ注入により、条件に合う依頼では Claude 側から /cadence を提案する運用。

## 完了（直近）
- 2026-07-06: 大規模改善8コミット（フィクスチャ実走 13/13 検出・バリデータ・readonly hook・収束決定論化・PJローカルフロー対応・トリアージ注入）→ [checkpoint](docs/checkpoints/2026-07-06.md)

## 次にやること
1. **各業務PJへのドメインフロー蒸留**（`references/flow-authoring.md` の手順で。各PJの環境PCで実施）
2. **実 infra MCP を繋いだ実走**（HANDOFF §4 の残項目。MCP 接続済みPCで）
3. **readonly-guard hook の有効化**（opt-in。install.sh が表示する設定を各PCの `~/.claude/settings.json` に追記）
4. **review/ABORT 経路の発火検証**（adversarial フィクスチャが要る → IMPROVEMENTS.md 参照）
5. （任意）gates・quorum 外注の実地検証

## ブロッカー
なし。2は MCP 接続済みPC、1は各業務PCでの作業が前提（このPCでは進められない）。

## 運用メモ
- 進行記録はこのファイル＋`docs/checkpoints/`。ハーネス改善ネタは `IMPROVEMENTS.md`（symlink 経由で全セッションから追記可）。
- Git: CLAUDE.local.md で1作業ごと自動 push をオプトイン済み（このPCのみ。他PCでは各自作成）。
