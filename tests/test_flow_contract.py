import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FlowContractTest(unittest.TestCase):
    def test_reliability_flow_keeps_bidirectional_alert_runbook_coverage(self):
        flow = (ROOT / "skills" / "cadence" / "flows" / "audit-reliability.md").read_text(
            encoding="utf-8"
        )
        plan = flow.split("### plan", 1)[1].split("### audit", 1)[0]
        audit = flow.split("### audit", 1)[1].split("### supervise", 1)[0]
        supervise = flow.split("### supervise", 1)[1].split("### review", 1)[0]
        persona = (
            ROOT / "skills" / "cadence" / "references" / "personas" / "sre-reviewer.md"
        ).read_text(encoding="utf-8")

        self.assertIn("相互対応", plan)
        self.assertIn("runbook↔alert対応表", audit)
        self.assertIn("各P1/P2 runbook", audit)
        self.assertIn("各paging alert", audit)
        self.assertIn("runbook↔alert対応表", supervise)
        self.assertIn("Bidirectional alert/runbook coverage", persona)

    def test_readonly_runs_record_hook_verification_state(self):
        claude_skill = (ROOT / "skills" / "cadence" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        codex_skill = (ROOT / "skills" / "codex-cadence" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        report_template = (
            ROOT / "skills" / "cadence" / "references" / "report-template.md"
        ).read_text(encoding="utf-8")

        for document in (claude_skill, codex_skill, report_template):
            self.assertIn("readonly_hook_status", document)
            self.assertIn("readonly_hook_deny", document)
        self.assertIn("/hooks", codex_skill)
        self.assertIn("trusted/enabled", codex_skill)


if __name__ == "__main__":
    unittest.main()
