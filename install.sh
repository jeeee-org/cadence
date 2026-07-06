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

# グローバル CLAUDE.md に cadence トリアージのブロックを注入する
# （正本は rules/cadence-triage.md。マーカー間を置換、無ければ末尾に追記。quorum-triage と同方式）
RULES_FILE="$SRC_DIR/rules/cadence-triage.md"
TARGET_MD="$CLAUDE_CONFIG_DIR/CLAUDE.md"
if [ -f "$RULES_FILE" ]; then
  if [ -f "$TARGET_MD" ] && grep -q 'cadence-triage:begin' "$TARGET_MD"; then
    awk -v rules="$RULES_FILE" '
      /cadence-triage:begin/ {skip=1; while ((getline line < rules) > 0) print line; close(rules); next}
      /cadence-triage:end/   {skip=0; next}
      !skip {print}
    ' "$TARGET_MD" > "$TARGET_MD.tmp" && mv "$TARGET_MD.tmp" "$TARGET_MD"
  else
    { [ -s "$TARGET_MD" ] && echo ""; cat "$RULES_FILE"; } >> "$TARGET_MD"
  fi
  echo "  - CLAUDE.md に cadence-triage ブロックを反映"
fi

echo "✓ インストール完了: $CLAUDE_CONFIG_DIR"
echo "  - skills/cadence"
echo "  - skills/cadence/IMPROVEMENTS.md -> $SRC_DIR/IMPROVEMENTS.md (symlink)"
echo "  - commands/cadence.md"
echo ""
echo "Claude Code を再起動するか /reload-skills を実行してください。"
echo ""
echo "（opt-in）read-only をハーネス側で強制するには ~/.claude/settings.json の hooks に追記:"
echo '  {"hooks": {"PreToolUse": [{"matcher": "Edit|Write|NotebookEdit",'
echo '    "hooks": [{"type": "command",'
echo "      \"command\": \"python3 $CLAUDE_CONFIG_DIR/skills/cadence/hooks/readonly-guard.py\"}]}]}}"
echo "  詳細: skills/cadence/hooks/readonly-guard.py 冒頭コメント"
