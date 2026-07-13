import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallTest(unittest.TestCase):
    def test_installs_both_hosts_idempotently(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            claude_home = temp_path / ".claude"
            codex_home = temp_path / ".codex"
            claude_home.mkdir()
            codex_home.mkdir()
            (claude_home / "CLAUDE.md").write_text("claude-user-rule\n", encoding="utf-8")
            (codex_home / "AGENTS.md").write_text("codex-user-rule\n", encoding="utf-8")

            env = os.environ.copy()
            env.update({
                "HOME": str(temp_path),
                "CLAUDE_CONFIG_DIR": str(claude_home),
                "CODEX_HOME": str(codex_home),
            })
            for _ in range(2):
                subprocess.run(
                    ["bash", str(ROOT / "install.sh")],
                    cwd=ROOT,
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            claude_skill = claude_home / "skills" / "cadence"
            codex_skill = codex_home / "skills" / "cadence"
            self.assertIn("Claude Code スキル", (claude_skill / "SKILL.md").read_text())
            self.assertIn("# Cadence for Codex", (codex_skill / "SKILL.md").read_text())
            self.assertTrue((codex_skill / "flows" / "audit-reliability.md").is_file())
            self.assertTrue((codex_skill / "references" / "report-template.md").is_file())
            self.assertTrue((codex_skill / "hooks" / "readonly-guard.py").is_file())
            self.assertIn("$cadence", (codex_skill / "agents" / "openai.yaml").read_text())
            self.assertEqual(
                (codex_skill / "IMPROVEMENTS.md").resolve(),
                (ROOT / "IMPROVEMENTS.md").resolve(),
            )
            self.assertEqual(
                (claude_skill / "IMPROVEMENTS.md").resolve(),
                (ROOT / "IMPROVEMENTS.md").resolve(),
            )

            claude_rules = (claude_home / "CLAUDE.md").read_text()
            codex_rules = (codex_home / "AGENTS.md").read_text()
            self.assertIn("claude-user-rule", claude_rules)
            self.assertIn("codex-user-rule", codex_rules)
            self.assertEqual(claude_rules.count("cadence-triage:begin"), 1)
            self.assertEqual(codex_rules.count("cadence-triage:begin"), 1)
            self.assertIn("利用可能な `$cadence`", codex_rules)


if __name__ == "__main__":
    unittest.main()
