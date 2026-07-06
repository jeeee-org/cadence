#!/usr/bin/env python3
"""cadence read-only ガード（PreToolUse hook）。

read-only フローのラン中だけ Edit/Write/NotebookEdit を物理的に拒否する。
「指示遵守は最弱の層」（SKILL.md「read-only の担保方針」）をハーネス強制に格上げする層。

仕組み:
  - エンジンは read-only フローのラン開始時に <target-repo>/.cadence/readonly
    （センチネルファイル）を作り、ラン終了（COMPLETE/ABORT）時に消す。
  - このフックはセンチネルが存在する間だけ発動し、.cadence/ 配下（ラン成果物）
    以外への Edit/Write/NotebookEdit を deny する。
  - センチネルが無ければ何もしない（通常作業に影響ゼロ）。

導入（opt-in）: ~/.claude/settings.json の hooks に追記
  {"hooks": {"PreToolUse": [{"matcher": "Edit|Write|NotebookEdit",
    "hooks": [{"type": "command",
      "command": "python3 ~/.claude/skills/cadence/hooks/readonly-guard.py"}]}]}}
"""
import json
import sys
from pathlib import Path


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # 入力が読めないときは邪魔をしない

    cwd = Path(data.get("cwd") or ".").resolve()
    sentinel = cwd / ".cadence" / "readonly"
    if not sentinel.exists():
        return 0  # ラン中でなければ何もしない

    tool_input = data.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if target:
        try:
            # ラン成果物（.cadence/ 配下）への書き込みは許可
            Path(target).resolve().relative_to(cwd / ".cadence")
            return 0
        except ValueError:
            pass

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "cadence の read-only ランが進行中です（.cadence/readonly が存在）。"
                ".cadence/ 配下（ラン成果物）以外への Edit/Write/NotebookEdit はブロックされます。"
                "指摘・リスク・修正案はレポートに書いてください。ランが終了しているのに"
                "このメッセージが出る場合は .cadence/readonly を削除してください。"
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
