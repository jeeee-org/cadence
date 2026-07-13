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
            result = None
            for _ in range(2):
                result = subprocess.run(
                    ["bash", str(ROOT / "install.sh")],
                    cwd=ROOT,
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            self.assertIsNotNone(result)
            self.assertIn("/hooks", result.stdout)
            self.assertIn("review/trust", result.stdout)
            self.assertIn("trusted/enabled", result.stdout)
            self.assertNotIn("AGENTS.override.md", result.stderr)

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

    def test_warns_when_codex_agents_override_masks_managed_block(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            claude_home = temp_path / ".claude"
            codex_home = temp_path / ".codex"
            claude_home.mkdir()
            codex_home.mkdir()
            (codex_home / "AGENTS.override.md").write_text(
                "local override\n", encoding="utf-8"
            )

            env = os.environ.copy()
            env.update({
                "HOME": str(temp_path),
                "CLAUDE_CONFIG_DIR": str(claude_home),
                "CODEX_HOME": str(codex_home),
            })
            result = subprocess.run(
                ["bash", str(ROOT / "install.sh")],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn(str(codex_home / "AGENTS.override.md"), result.stderr)
            self.assertIn("AGENTS.md", result.stderr)
            self.assertIn("手動で統合", result.stderr)
            self.assertIn(
                "cadence-triage:begin",
                (codex_home / "AGENTS.md").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
