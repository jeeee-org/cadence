#!/usr/bin/env python3
"""cadence フロー定義（flows/*.md）の決定論バリデータ。

cadence 自身の思想（LLM 判定でなく exit code で機械判定）を自分に適用する層。
壊れたフロー定義を実行時のエンジン解釈で握り潰さず、コミット前/インストール時に弾く。

チェック内容:
  1. yaml ブロックに mode(read-only|edit) / initial / max_cycles がある
  2. initial が定義済み step を指す
  3. 全遷移先（next の → `X`、gates の on_fail）が定義済み step か COMPLETE/ABORT
  4. 各 step の persona が references/personas/<persona>.md に実在する
  5. 各 step に next（遷移）が最低1つある
  6. mode: read-only のフローに edit: yes の step が無い
  7. require_human_approval: true のフローに human_approval: required の step がある
  8. initial から全 step へ到達可能（unreachable step の検出）

使い方:
  scripts/validate-flows.py [--skill-dir skills/cadence]
  scripts/validate-flows.py --project-dir <PJルート>   # <PJ>/.claude/cadence/flows/ を検証
                                                       # （persona は PJ→同梱の順で解決）
exit code: 0=全フロー合格 / 1=違反あり
"""
import argparse
import re
import sys
from pathlib import Path

TERMINALS = {"COMPLETE", "ABORT"}


def parse_flow(text: str):
    """フロー MD から (front, steps) を抜く。steps は {name: 本文} の dict。"""
    front = {}
    m = re.search(r"```yaml\n(.*?)```", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            kv = re.match(r"^(\w+):\s*(.*?)\s*(?:#.*)?$", line)
            if kv:
                front[kv.group(1)] = kv.group(2).strip()

    steps = {}
    steps_sec = re.search(r"^## steps\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if steps_sec:
        for sm in re.finditer(
            r"^### (\S+)\n(.*?)(?=^### |\Z)", steps_sec.group(1), re.S | re.M
        ):
            steps[sm.group(1)] = sm.group(2)
    return front, steps


def validate(flow_path: Path, personas_dirs: list):
    errors = []
    text = flow_path.read_text(encoding="utf-8")
    front, steps = parse_flow(text)

    # 1. 必須フィールド
    mode = front.get("mode")
    if mode not in ("read-only", "edit"):
        errors.append(f"mode が read-only|edit でない: {mode!r}")
    initial = front.get("initial")
    if not initial:
        errors.append("initial が無い")
    mc = front.get("max_cycles", "")
    if not re.match(r"^\d+$", mc):
        errors.append(f"max_cycles が整数でない: {mc!r}")

    if not steps:
        errors.append("## steps に step（### 見出し）が無い")
        return errors

    # 2. initial の実在
    if initial and initial not in steps:
        errors.append(f"initial: {initial} が step に無い")

    valid_targets = set(steps) | TERMINALS

    for name, body in steps.items():
        # 4. persona の実在
        pm = re.search(r"\*\*persona\*\*:\s*(\S+)", body)
        if not pm:
            errors.append(f"step {name}: persona が無い")
        elif not any((d / f"{pm.group(1)}.md").exists() for d in personas_dirs):
            dirs = " / ".join(str(d) for d in personas_dirs)
            errors.append(f"step {name}: persona '{pm.group(1)}' が {dirs} のいずれにも無い")

        # 3. 遷移先の実在 / 5. next の存在
        targets = re.findall(r"→\s*`([^`]+)`", body)
        if not targets:
            errors.append(f"step {name}: next（→ `X` 形式の遷移）が1つも無い")
        for t in targets:
            if t not in valid_targets:
                errors.append(f"step {name}: 遷移先 `{t}` が未定義（steps にも COMPLETE/ABORT にも無い）")

        # 6. read-only フローに edit: yes が無い
        if mode == "read-only" and re.search(r"\*\*edit\*\*:\s*yes", body):
            errors.append(f"step {name}: mode: read-only なのに edit: yes")

    # 3'. gates の on_fail
    for gm in re.finditer(r"on_fail:\s*(\S+)", text):
        t = gm.group(1)
        if t not in valid_targets:
            errors.append(f"gates: on_fail の遷移先 `{t}` が未定義")

    # 7. 有人承認の整合
    if front.get("require_human_approval") == "true":
        if not re.search(r"\*\*human_approval\*\*:\s*required", text):
            errors.append("require_human_approval: true だが human_approval: required の step が無い")

    # 8. 到達可能性
    if initial in steps:
        reachable, frontier = set(), [initial]
        while frontier:
            cur = frontier.pop()
            if cur in reachable or cur in TERMINALS:
                continue
            reachable.add(cur)
            frontier += re.findall(r"→\s*`([^`]+)`", steps.get(cur, ""))
        for name in set(steps) - reachable:
            errors.append(f"step {name}: initial({initial}) から到達不能")

    return errors


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    default_skill = Path(__file__).resolve().parent.parent / "skills" / "cadence"
    ap.add_argument("--skill-dir", type=Path, default=default_skill)
    ap.add_argument("--project-dir", type=Path, default=None,
                    help="PJルート。<PJ>/.claude/cadence/flows/ を検証（persona は PJ→同梱の順で解決）")
    args = ap.parse_args()

    # persona の解決順：PJローカル →（このリポの）同梱 → インストール済みグローバル
    personas_dirs = [
        args.skill_dir / "references" / "personas",
        Path.home() / ".claude" / "skills" / "cadence" / "references" / "personas",
    ]
    if args.project_dir:
        flows_dir = args.project_dir / ".claude" / "cadence" / "flows"
        personas_dirs.insert(0, args.project_dir / ".claude" / "cadence" / "personas")
    else:
        flows_dir = args.skill_dir / "flows"

    flows = sorted(flows_dir.glob("*.md"))
    if not flows:
        print(f"NG: フローが見つからない: {flows_dir}", file=sys.stderr)
        return 1

    failed = False
    for f in flows:
        errs = validate(f, personas_dirs)
        if errs:
            failed = True
            print(f"NG {f.name}")
            for e in errs:
                print(f"   - {e}")
        else:
            print(f"OK {f.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
