"""Focused validation of a completed private 0x002C00D4 experiment report."""
import json
import sys
import unittest
from pathlib import Path


class AsdFlagExperimentReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if len(sys.argv) < 2:
            raise RuntimeError("pass the private experiment report.json path")
        cls.report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

    def test_reference_boundary_and_padding(self):
        boundary = self.report["boundary"]
        self.assertEqual(boundary["return_address"], "0x002c00e4")
        self.assertEqual(boundary["trailing_halfword"], "0xffff")
        self.assertFalse(boundary["trailing_halfword_executed"])

    def test_directed_values_and_aligned_boundaries_are_present(self):
        labels = {case["label"] for case in self.report["cases"]}
        self.assertTrue({"zero", "one", "positive", "high-bit", "negative-u32",
                         "signed-min", "max-positive"}.issubset(labels))
        self.assertEqual(self.report["case_count"], len(self.report["cases"]))
        self.assertTrue(all(case["pointer_offset"] % 4 == 0 for case in self.report["cases"]))

    def test_original_candidate_differential_and_wrong_control(self):
        self.assertTrue(self.report["passed"])
        self.assertTrue(all(case["passed"] for case in self.report["cases"]))
        control = self.report["negative_control"]
        self.assertEqual(control["name"], "missing-store")
        self.assertTrue(control["detected"])

    def test_callers_consume_return_polarity(self):
        callers = self.report["caller_evidence"]
        self.assertGreaterEqual(len(callers), 2)
        self.assertTrue(all("cmp r0,#0" in caller["observed_use"] for caller in callers))


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
