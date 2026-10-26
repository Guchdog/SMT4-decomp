from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPORT = (ROOT / "build/agent-work/H1-semantic/h1-animation-row-setter-candidate/"
          "overnight-20261025-animation-row-setter/run-02/report.json")


class AnimationRowSetterExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not REPORT.is_file():
            raise AssertionError("run tools/h1_animation_row_setter_experiment.py first")
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_valid_pointer_cases_match_pinned_arm(self):
        self.assertTrue(self.report["passed"])
        self.assertEqual(self.report["case_count"], 9)
        self.assertTrue(all(case["passed"] for case in self.report["cases"]))
        self.assertIsNone(self.report["first_mismatch"])

    def test_null_object_fault_is_separate_from_valid_domain(self):
        case = self.report["cases"][0]
        self.assertTrue(case["expected_fault"])
        self.assertIsNotNone(case["original"]["fault"])
        self.assertIsNotNone(case["candidate"]["fault"])

    def test_negative_control_detects_missing_completion_clear(self):
        control = self.report["negative_controls"][0]
        self.assertEqual(control["name"], "missing_0x86_clear")
        self.assertTrue(control["detected"])
        self.assertIn("synthetic memory differs", control["errors"])

    def test_boundary_and_stride_cases_are_present(self):
        names = {case["name"] for case in self.report["cases"]}
        self.assertIn("row index one uses 12-byte table stride", names)
        self.assertIn("negative row index selects preceding row by wrapped address", names)
        self.assertIn("signed coordinate minimum and maximum mode zero", names)
        self.assertIn("signed coordinate maximum and minimum mode nonzero", names)
        self.assertIn("nonnull object with null table returns unchanged", names)


if __name__ == "__main__":
    unittest.main()
