#!/usr/bin/env bash
# cadence をローカルの Claude Code 設定に配置する。
#   skills/cadence -> $CLAUDE_CONFIG_DIR/skills/cadence
#   commands/*     -> $CLAUDE_CONFIG_DIR/commands/
# 配置先を変えたい場合: CLAUDE_CONFIG_DIR=/path/.claude ./install.sh
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

mkdir -p "$CLAUDE_CONFIG_DIR/skills" "$CLAUDE_CONFIG_DIR/commands"

# スキル本体をコピー
rm -rf "$CLAUDE_CONFIG_DIR/skills/cadence"
cp -R "$SRC_DIR/skills/cadence" "$CLAUDE_CONFIG_DIR/skills/cadence"

# スラッシュコマンドをコピー
cp "$SRC_DIR"/commands/*.md "$CLAUDE_CONFIG_DIR/commands/"

echo "✓ インストール完了: $CLAUDE_CONFIG_DIR"
echo "  - skills/cadence"
echo "  - commands/cadence.md"
echo ""
echo "Claude Code を再起動するか /reload-skills を実行してください。"
