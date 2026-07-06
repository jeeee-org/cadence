#!/usr/bin/env bash
# cadence をローカルの Claude Code 設定に配置する。
#   skills/cadence -> $CLAUDE_CONFIG_DIR/skills/cadence
#   commands/*     -> $CLAUDE_CONFIG_DIR/commands/
# 配置先を変えたい場合: CLAUDE_CONFIG_DIR=/path/.claude ./install.sh
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

# フロー定義を機械検証してから配置する（壊れたフローを実行時に持ち込まない）
if command -v python3 >/dev/null 2>&1; then
  python3 "$SRC_DIR/scripts/validate-flows.py" || {
    echo "✗ フロー定義の検証に失敗。修正してから再実行してください。" >&2
    exit 1
  }
else
  echo "⚠ python3 が無いためフロー検証をスキップ（scripts/validate-flows.py）" >&2
fi

mkdir -p "$CLAUDE_CONFIG_DIR/skills" "$CLAUDE_CONFIG_DIR/commands"

# スキル本体をコピー
rm -rf "$CLAUDE_CONFIG_DIR/skills/cadence"
cp -R "$SRC_DIR/skills/cadence" "$CLAUDE_CONFIG_DIR/skills/cadence"

# IMPROVEMENTS.md はリポ root（$SRC_DIR/IMPROVEMENTS.md）を正本にし、install 先は symlink。
# 実行時の追記が git 管理下のリポ側へ書き込まれ、再インストールの rm -rf でも消えない。
ln -sfn "$SRC_DIR/IMPROVEMENTS.md" "$CLAUDE_CONFIG_DIR/skills/cadence/IMPROVEMENTS.md"

# スラッシュコマンドをコピー
cp "$SRC_DIR"/commands/*.md "$CLAUDE_CONFIG_DIR/commands/"

echo "✓ インストール完了: $CLAUDE_CONFIG_DIR"
echo "  - skills/cadence"
echo "  - skills/cadence/IMPROVEMENTS.md -> $SRC_DIR/IMPROVEMENTS.md (symlink)"
echo "  - commands/cadence.md"
echo ""
echo "Claude Code を再起動するか /reload-skills を実行してください。"
