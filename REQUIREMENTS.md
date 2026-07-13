# REQUIREMENTS

## 目的

cadence を Claude Code と Codex の双方から利用可能にし、同じフロー・ペルソナ・収束規約・監査証跡を共有する。

## 対象

- `install.sh` から Claude Code と Codex の設定領域へ、それぞれのスキルとトリアージ連携を冪等に配置する。
- Codexでは `$cadence` の明示指定、または `claude-rules` の `CADENCE` 分類から対応フローを実行する。
- Codex版は直接サブエージェント、`apply_patch`、web、shell、MCPなど、そのセッションで実際に利用可能な能力へフローの抽象ツール名を写像する。
- PJローカルのドメインフローは `<PJ>/.agents/cadence/` を第一候補とし、既存 `<PJ>/.claude/cadence/` を後方互換で読む。
- read-onlyフローはMCP/資格情報/環境の物理境界を優先し、ローカル編集はopt-in hookと指示規律を重ねる。hookは実行cwd基準で対象を解決し、`.cadence/runs/`だけを許可してセンチネル自身を保護する。探索範囲はcwdから最初のGitルートまでとし、run証跡にはhook確認状態を残す。
- Claude/Codex両方のインストール、マーカー更新、既存グローバル指示の保持、フロー解決、hook拒否をAPI不要のテストで検証する。Codexの非managed command hookは`/hooks`でのreview/trustが必要だと導入時に案内し、非空のglobal `AGENTS.override.md`が管理対象`AGENTS.md`を隠す場合は警告する。
- 合成フィクスチャでCodex版のフロー選択・状態記録・最終レポートまで実走確認する。

## 対象外

- Codexプラグイン／マーケットプレイスとしての配布。
- ライブ本番環境への書き込みや、実資格情報を使う自動E2E。
- `claude-rules` / `quorum` を含む全リポのスキル配置先を同時移行すること。

## 未決事項

- Codexユーザースキルの既定配置を、既存3リポが使う `$CODEX_HOME/skills` から公式推奨の `$HOME/.agents/skills` へ一括移行する時期。
- Codex hookが全shell経路を確実に遮断できるようになるまで、ローカルread-onlyをどの権限境界でさらに強制するか。
