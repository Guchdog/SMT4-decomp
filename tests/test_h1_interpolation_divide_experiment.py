"""Focused checks for a private 0x002C615C ARM differential report."""
import json
import sys
import unittest
from pathlib import Path


class InterpolationDivideReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if len(sys.argv) < 2:
            raise RuntimeError("pass the private report.json path")
        cls.report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

    def test_pinned_body_and_candidate_link(self):
        self.assertEqual(self.report["body_size"], 556)
        self.assertEqual(self.report["return_boundary"], "BX LR at 0x002C6384")
        self.assertEqual(self.report["candidate"]["undefined_symbols"], [])
        self.assertTrue(self.report["candidate"]["text_size"] > 0)

    def test_nonzero_domain_matches_and_covers_h1_inputs(self):
        self.assertTrue(self.report["passed"])
        self.assertTrue(all(row["passed"] for row in self.report["cases"]))
        self.assertEqual(self.report["nonzero_case_count"],
                         sum(row["denominator_bits"] != "0x0" for row in self.report["cases"]))
        self.assertTrue(all(row["passed"] for row in self.report["cases"]
                            if row["denominator_bits"] != "0x0"))
        self.assertTrue(all(row["original_r1_remainder"] == row["candidate_r1_remainder"]
                            for row in self.report["cases"]))
        memory = self.report["memory_summary"]
        self.assertEqual(memory["data_equal_case_count"], self.report["case_count"])
        self.assertEqual(memory["original_stack_changed_nonzero_case_count"], 0)
        self.assertGreater(memory["candidate_stack_changed_nonzero_case_count"], 0)
        h1 = [row for row in self.report["cases"] if row["label"] == "h1-delta-duration"]
        self.assertEqual(len(h1), 35)
        self.assertTrue(all(1 <= row["denominator_signed"] <= 65535 for row in h1))

    def test_zero_divisor_is_recorded_without_claiming_stack_identity(self):
        zero = self.report["zero_divisor_observation"]
        self.assertEqual(zero["original_r0_values"], ["0x0"])
        self.assertEqual(zero["candidate_r0_values"], ["0x0"])
        self.assertTrue(all(row["original_r1_remainder"] == row["candidate_r1_remainder"]
                            for row in zero["cases"]))
        self.assertTrue(zero["original_stack_writes_remain_after_return"])

    def test_wrong_quotient_control_is_detected(self):
        control = self.report["negative_control"]
        self.assertEqual(control["name"], "quotient-plus-one")
        self.assertTrue(control["detected"])
        self.assertIn("r0 quotient differs", control["case"]["errors"])


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
