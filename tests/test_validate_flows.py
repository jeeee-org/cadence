import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-flows.py"


def valid_flow(persona):
    return textwrap.dedent(f"""\
        # flow: custom

        ```yaml
        purpose: test
        mode: read-only
        initial: audit
        max_cycles: 1
        ```

        ## steps

        ### audit
        - **persona**: {persona}
        - **edit**: no
        - **next**:
          - 完了 → `COMPLETE`
        """)


class ValidateProjectFlowsTest(unittest.TestCase):
    def run_validator(self, project):
        env = os.environ.copy()
        env["CODEX_HOME"] = str(Path(project) / "fake-codex-home")
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--project-dir", str(project)],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )

    def test_agents_flow_overrides_same_named_legacy_flow(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            agents_flow = project / ".agents" / "cadence" / "flows"
            agents_persona = project / ".agents" / "cadence" / "personas"
            legacy_flow = project / ".claude" / "cadence" / "flows"
            agents_flow.mkdir(parents=True)
            agents_persona.mkdir(parents=True)
            legacy_flow.mkdir(parents=True)
            (agents_flow / "custom.md").write_text(valid_flow("domain"), encoding="utf-8")
            (agents_persona / "domain.md").write_text("# Domain\n", encoding="utf-8")
            (legacy_flow / "custom.md").write_text("invalid legacy flow\n", encoding="utf-8")

            result = self.run_validator(project)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("OK custom.md", result.stdout)

    def test_legacy_flow_remains_supported(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            legacy_flow = project / ".claude" / "cadence" / "flows"
            legacy_persona = project / ".claude" / "cadence" / "personas"
            legacy_flow.mkdir(parents=True)
            legacy_persona.mkdir(parents=True)
            (legacy_flow / "custom.md").write_text(valid_flow("legacy"), encoding="utf-8")
            (legacy_persona / "legacy.md").write_text("# Legacy\n", encoding="utf-8")

            result = self.run_validator(project)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_project_flows_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_validator(Path(temp))
            self.assertEqual(result.returncode, 1)
            self.assertIn(".agents", result.stderr)
            self.assertIn(".claude", result.stderr)


if __name__ == "__main__":
    unittest.main()
