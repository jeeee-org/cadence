# cadence PJ固有ルール

## 目的と最大リスク

- Claude Code / Codex をホストに、宣言的フローで plan → audit → supervise → review を回す cadence を配布・保守する。
- 最大のリスクは、ホスト固有のツール名・スキル配置・hook入力を混同して read-only 境界や有人承認を形骸化すること。

## 記録

- `REQUIREMENTS.md` は Claude/Codex 両ホストの機能要件・配布契約・互換性を管理する。
- 汎用ハーネスの改善候補は `IMPROVEMENTS.md`、確定した判断と罠は `NOTES.md`、詳細作業ログは日別 checkpoint に記録する。
- `.cadence/` は実走の一時証跡であり、リポジトリへコミットしない。

## Git

- リモートは `https://github.com/jeeee-org/cadence.git`。低リスクの個人リポとして `main` の直接編集と、作業単位の自動 push を許可する。
- コミットは日本語 subject と説明 body を使い、Claude版/Codex版にまたがる変更でも1つの利用者価値ごとにまとめる。

## 実装・検証

- Bash / Python標準ライブラリ / Markdown を中心にし、追加依存を安易に増やさない。
- Claude版とCodex版で flows / references / hook を共有し、ホスト固有の実行手順とUIメタデータだけを分離する。
- 変更後は `bash tests/run_tests.sh`、`bash -n install.sh tests/*.sh`、`python3 scripts/validate-flows.py` を実行する。
- Codex版スキルは skill validator でも検証し、インストール試験は一時ディレクトリだけを使う。
