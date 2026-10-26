"""Contract-specific tests for the isolated titleMain constructor candidate."""
from __future__ import annotations

import unittest
from pathlib import Path

from tools.h1_title_init_experiment import ROOT, run_experiment


class TestH1TitleInitExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        output = (ROOT / "build/agent-work/H1-semantic/h1-title-init-candidate/"
                  "sleep-20261025-title-init/checks/unittest")
        cls.report = run_experiment(ROOT / "extracted/exefs/code.bin", output)

    def test_null_and_every_argument_byte_match_original(self):
        self.assertTrue(self.report["passed"])
        self.assertEqual(self.report["nullable_argument_cases_compared"], 257)
        self.assertEqual(self.report["nullable_argument_domain"],
                         "null and all 256 byte values")
        self.assertIsNone(self.report["first_counterexample"])

    def test_allocation_and_task_callbacks_match_pinned_contract(self):
        contract = self.report["registration_contract"]
        self.assertEqual(len(contract), 5)
        self.assertEqual(contract[0]["r0_r3"], ["0x10000", "0x100", "0x0", "0xa0"])
        self.assertEqual(contract[0]["stack"], ["0x1"])
        self.assertEqual(contract[1]["name"], "TITLE C")
        self.assertEqual(contract[1]["stack"], ["0x1e989c", "0x2ca6f4", "0x0"])
        self.assertEqual([row["name"] for row in contract[2:]],
                         ["TITLE UDrawLeft", "TITLE UDrawRight", "TITLE D"])
        self.assertEqual([row["r0_r3"][1] for row in contract[2:]],
                         ["0x76", "0xd4", "0xe7"])
        self.assertTrue(all(row["mismatch"] is None
                            for row in self.report["preexisting_global_cases"]))

    def test_negative_control_is_caught_at_argument_dependent_flag(self):
        control = self.report["negative_control"]
        self.assertEqual(control["detected_difference"], "work differs")
        self.assertEqual(control["differing_work_offsets"], ["0x10"])
        self.assertEqual(control["original_flag_0x10"], "00")
        self.assertEqual(control["negative_flag_0x10"], "01")


if __name__ == "__main__":
    unittest.main()
