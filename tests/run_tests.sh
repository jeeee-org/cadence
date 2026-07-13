#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 scripts/validate-flows.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
bash -n install.sh tests/*.sh

SKILL_VALIDATOR="${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py"
if [ -f "$SKILL_VALIDATOR" ]; then
  python3 "$SKILL_VALIDATOR" skills/codex-cadence
else
  echo "SKIP: Codex skill validator が見つかりません: $SKILL_VALIDATOR" >&2
fi
