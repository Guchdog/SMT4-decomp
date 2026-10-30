from __future__ import annotations

import unittest
from pathlib import Path

from tools.h1_title_fade_experiment import ROOT, run_experiment


class H1TitleFadeExperimentTests(unittest.TestCase):
    def test_directed_differential_and_wrong_zero_boundary(self):
        code = ROOT / "build/azahar-validation/exefs/code.bin"
        self.assertTrue(code.is_file(), "pinned private code.bin is required")
        report_path = (ROOT / "build/agent-work/H1-semantic/h1-title-fade-s0-repair/"
                       "sleep-20261025-fade-s0/checks/unittest/report.json")
        report = run_experiment(code, report_path, ROOT / "build/agent-work")
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["cases"]), 15)
        self.assertTrue(all(row["passed"] for row in report["cases"]))
        self.assertTrue(all("return_r0" in row for row in report["cases"]))
        self.assertTrue(all(row["return_s0"] == "0x3f400000" for row in report["cases"]))
        self.assertEqual(len(report["s0_restoration_cases"]), 2)
        self.assertTrue(all(row["passed"] for row in report["s0_restoration_cases"]))
        self.assertTrue(all(row["original_return_s0"] == "0x3f400000"
                            and row["candidate_return_s0"] == "0x3f400000"
                            and row["seam_event"]["after"] == "0x41200000"
                            for row in report["s0_restoration_cases"]))
        self.assertEqual([row["reached_positive_continuation"]
                          for row in report["s0_restoration_cases"]], [False, True])
        self.assertTrue(report["adversarial_mutation"]["passed"])
        self.assertEqual(len(report["adversarial_mutation"]["seams"]), 2)
        self.assertEqual(report["adversarial_mutation"]["calls"][1]["r0"], "0x2000600")
        self.assertEqual(report["adversarial_mutation"]["calls"][2]["r0"], "0x2000700")
        event_kinds = [row["kind"] for row in report["adversarial_mutation"]["events"]]
        self.assertEqual(event_kinds, ["direct_entry", "positive_body", "callback",
                                      "direct_entry", "direct_entry"])
        self.assertEqual(report["adversarial_mutation"]["events"][2]["s0"], "0x3f000000")
        self.assertTrue(report["negative_control"]["passed"])
        self.assertEqual(report["negative_control"]["first_difference"], "calls differs")
        self.assertTrue(report_path.is_file())


if __name__ == "__main__":
    unittest.main()
