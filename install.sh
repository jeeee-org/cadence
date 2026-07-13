#!/usr/bin/env bash
# cadence をローカルの Claude Code / Codex 設定に配置する。
#   skills/cadence -> $CLAUDE_CONFIG_DIR/skills/cadence
#   skills/cadence + Codex差分 -> $CODEX_HOME/skills/cadence
#   commands/*     -> $CLAUDE_CONFIG_DIR/commands/
# 配置先を変えたい場合: CLAUDE_CONFIG_DIR=/path/.claude CODEX_HOME=/path/.codex ./install.sh
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

# フロー定義を機械検証してから配置する（壊れたフローを実行時に持ち込まない）
if command -v python3 >/dev/null 2>&1; then
  python3 "$SRC_DIR/scripts/validate-flows.py" || {
    echo "✗ フロー定義の検証に失敗。修正してから再実行してください。" >&2
    exit 1
  }
else
  echo "⚠ python3 が無いためフロー検証をスキップ（scripts/validate-flows.py）" >&2
fi

mkdir -p "$CLAUDE_CONFIG_DIR/skills" "$CLAUDE_CONFIG_DIR/commands" "$CODEX_HOME/skills"

# スキル本体をコピー
rm -rf "$CLAUDE_CONFIG_DIR/skills/cadence"
cp -R "$SRC_DIR/skills/cadence" "$CLAUDE_CONFIG_DIR/skills/cadence"

# IMPROVEMENTS.md はリポ root（$SRC_DIR/IMPROVEMENTS.md）を正本にし、install 先は symlink。
# 実行時の追記が git 管理下のリポ側へ書き込まれ、再インストールの rm -rf でも消えない。
ln -sfn "$SRC_DIR/IMPROVEMENTS.md" "$CLAUDE_CONFIG_DIR/skills/cadence/IMPROVEMENTS.md"

# Codex版は共有flows/references/hookをコピーし、ホスト固有のSKILL.md / agentsを上書きする。
rm -rf "$CODEX_HOME/skills/cadence"
cp -R "$SRC_DIR/skills/cadence" "$CODEX_HOME/skills/cadence"
cp "$SRC_DIR/skills/codex-cadence/SKILL.md" "$CODEX_HOME/skills/cadence/SKILL.md"
rm -rf "$CODEX_HOME/skills/cadence/agents"
cp -R "$SRC_DIR/skills/codex-cadence/agents" "$CODEX_HOME/skills/cadence/agents"
ln -sfn "$SRC_DIR/IMPROVEMENTS.md" "$CODEX_HOME/skills/cadence/IMPROVEMENTS.md"

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

# CodexグローバルAGENTS.mdには分類を複製せず、CADENCEと$cadenceの接続だけを置く。
CODEX_TARGET_MD="$CODEX_HOME/AGENTS.md"
CODEX_RULES_FILE="$SRC_DIR/rules/codex-cadence-triage.md"
CODEX_MARK_BEGIN='<!-- cadence-triage:begin (cadence/install.sh Codex版が管理。手動編集しない — 変更はリポの rules/codex-cadence-triage.md へ) -->'
CODEX_MARK_END='<!-- cadence-triage:end -->'
touch "$CODEX_TARGET_MD"
if grep -qF -- "$CODEX_MARK_BEGIN" "$CODEX_TARGET_MD"; then
  awk -v begin="$CODEX_MARK_BEGIN" -v end="$CODEX_MARK_END" -v rulefile="$CODEX_RULES_FILE" '
    $0 == begin { print; while ((getline line < rulefile) > 0) print line; close(rulefile); skip = 1; next }
    $0 == end   { skip = 0; print; next }
    !skip       { print }
  ' "$CODEX_TARGET_MD" > "$CODEX_TARGET_MD.tmp" && mv "$CODEX_TARGET_MD.tmp" "$CODEX_TARGET_MD"
else
  { [ -s "$CODEX_TARGET_MD" ] && echo ""; echo "$CODEX_MARK_BEGIN"; cat "$CODEX_RULES_FILE"; echo "$CODEX_MARK_END"; } >> "$CODEX_TARGET_MD"
fi

# グローバル指示の常時ロード上限を目安チェック（超過してもインストールは継続）。
for global_doc in "$TARGET_MD" "$CODEX_TARGET_MD"; do
  global_size=$(wc -c < "$global_doc")
  if [ "$global_size" -gt 14336 ]; then
    echo "⚠ $global_doc が14KBを超過（${global_size} bytes）。ルール圧縮を検討してください。" >&2
  fi
done

echo "✓ インストール完了: $CLAUDE_CONFIG_DIR"
echo "  - skills/cadence"
echo "  - skills/cadence/IMPROVEMENTS.md -> $SRC_DIR/IMPROVEMENTS.md (symlink)"
echo "  - $CODEX_HOME/skills/cadence（Codex版）"
echo "  - $CODEX_HOME/skills/cadence/IMPROVEMENTS.md -> $SRC_DIR/IMPROVEMENTS.md (symlink)"
echo "  - commands/cadence.md"
echo "  - $CODEX_TARGET_MD の cadence-triage ブロック（CADENCE → \$cadence 連携）"
echo ""
echo "Claude Code を再起動するか /reload-skills を実行してください。Codexで反映されない場合は再起動してください。"
echo ""
echo "（opt-in）read-only をハーネス側で強制するには ~/.claude/settings.json の hooks に追記:"
echo '  {"hooks": {"PreToolUse": [{"matcher": "Edit|Write|NotebookEdit",'
echo '    "hooks": [{"type": "command",'
echo "      \"command\": \"python3 $CLAUDE_CONFIG_DIR/skills/cadence/hooks/readonly-guard.py\"}]}]}}"
echo "  詳細: skills/cadence/hooks/readonly-guard.py 冒頭コメント"
echo ""
echo "（opt-in）Codexでは $CODEX_HOME/hooks.json の PreToolUse matcher に apply_patch|Edit|Write を登録:"
echo "  command: python3 $CODEX_HOME/skills/cadence/hooks/readonly-guard.py"
echo "  Codexを再起動後、/hooks でこのcommand hookをreview/trustし、trusted/enabledを確認してください。"
echo "  未trustのcommand hookは実行されません。command定義を変更した場合は再度review/trustが必要です。"
echo "  ※ hookはshell書込みの全経路を遮断しないため、参照専用MCP・read-only資格情報を優先してください。"
