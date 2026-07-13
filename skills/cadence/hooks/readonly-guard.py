#!/usr/bin/env python3
"""cadence read-only ガード（Claude Code / Codex PreToolUse hook）。

read-only フローのラン中だけ Edit/Write/NotebookEdit/apply_patch を拒否する。
「指示遵守は最弱の層」（SKILL.md「read-only の担保方針」）をハーネス強制に格上げする層。

仕組み:
  - エンジンは read-only フローのラン開始時に <target-repo>/.cadence/readonly
    （センチネルファイル）を作り、ラン終了（COMPLETE/ABORT）時に消す。
  - このフックはセンチネルが存在する間だけ発動し、.cadence/ 配下（ラン成果物）
    以外への Edit/Write/NotebookEdit/apply_patch を deny する。
  - センチネルが無ければ何もしない（通常作業に影響ゼロ）。

導入（opt-in）: ~/.claude/settings.json の hooks に追記
  {"hooks": {"PreToolUse": [{"matcher": "Edit|Write|NotebookEdit",
    "hooks": [{"type": "command",
      "command": "python3 ~/.claude/skills/cadence/hooks/readonly-guard.py"}]}]}}

Codex: ~/.codex/hooks.json の PreToolUse に matcher "apply_patch|Edit|Write" で登録し、
  command を "python3 ~/.codex/skills/cadence/hooks/readonly-guard.py" にする。

注意: Codex hookは一部shell実行を完全には捕捉しない。参照専用MCP・read-only資格情報・
書込み不能環境を第一境界とし、このhookだけを物理境界とみなさない。
"""
import json
import re
import sys
from pathlib import Path


PATCH_PATH_RE = re.compile(
    r"^\*\*\* (?:Add|Update|Delete) File:\s*(.+?)\s*$|^\*\*\* Move to:\s*(.+?)\s*$"
)


def find_run_root(cwd: Path):
    """cwdからGitルートまで遡り、read-onlyセンチネルがあるランルートを返す。"""
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".cadence" / "readonly").exists():
            return candidate
        if (candidate / ".git").exists():
            break
    return None


def extract_target_paths(data):
    """Claudeのfile_path形式とCodex apply_patchのpatch headerを同じ列へ正規化する。"""
    tool_input = data.get("tool_input") or {}
    targets = []
    for key in ("file_path", "notebook_path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            targets.append(value.strip())

    command = tool_input.get("command")
    if isinstance(command, str):
        for line in command.splitlines():
            match = PATCH_PATH_RE.match(line)
            if match:
                targets.append((match.group(1) or match.group(2)).strip())
    return targets


def is_run_artifact(run_root: Path, raw_target: str):
    target = Path(raw_target)
    if not target.is_absolute():
        target = run_root / target
    try:
        target.resolve().relative_to((run_root / ".cadence").resolve())
        return True
    except (OSError, ValueError):
        return False


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # 入力が読めないときは邪魔をしない

    cwd = Path(data.get("cwd") or ".").resolve()
    run_root = find_run_root(cwd)
    if run_root is None:
        return 0  # ラン中でなければ何もしない

    targets = extract_target_paths(data)
    if targets and all(is_run_artifact(run_root, target) for target in targets):
        return 0  # ラン成果物（.cadence/ 配下）だけへの書き込みは許可

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "cadence の read-only ランが進行中です（.cadence/readonly が存在）。"
                ".cadence/ 配下（ラン成果物）以外への Edit/Write/NotebookEdit/apply_patch はブロックされます。"
                "指摘・リスク・修正案はレポートに書いてください。ランが終了しているのに"
                "このメッセージが出る場合は .cadence/readonly を削除してください。"
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
