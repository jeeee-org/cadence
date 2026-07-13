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


if __name__ == "__main__":
    unittest.main()
