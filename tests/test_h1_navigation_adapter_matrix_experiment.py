"""Assertions for the exhaustive bounded H1 navigation adapter matrix."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "build/agent-work/H1-semantic/h1-navigation-adapter-matrix/overnight-20261025-navigation-matrix/results-v2/report.json"


class NavigationAdapterMatrixReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_complete_mask_cursor_cache_cartesian_product(self):
        report = self.report
        rows = report["matrix_cases"]
        self.assertEqual(len(rows), 256)
        self.assertEqual(report["matrix_definition"]["matrix_case_count"], 256)
        self.assertTrue(report["passed"])
        self.assertIsNone(report["first_mismatch"])
        self.assertTrue(all(row["passed"] and row["ordered_observations_match"] for row in rows))
        tuples = {(row["input"]["cursor"], row["input"]["cached"], row["input"]["mask"])
                  for row in rows}
        self.assertEqual(tuples, {(cursor, cached, mask)
                                  for cursor in range(4) for cached in range(4)
                                  for mask in range(16)})

    def test_gate_false_and_wrong_normalization_control(self):
        report = self.report
        gates = {row["case"]: row for row in report["gate_false_cases"]}
        self.assertEqual(set(gates), {"script_not_ready", "preview_not_ready"})
        self.assertTrue(all(row["passed"] for row in gates.values()))
        self.assertEqual(gates["script_not_ready"]["ordered_observations"]["triggers"], [])
        self.assertEqual(gates["preview_not_ready"]["ordered_observations"]["triggers"], [])

        control = report["negative_control"]
        self.assertTrue(control["detected"])
        self.assertEqual(control["expected_original_selection"], 3)
        self.assertEqual(control["mutant_selection"], 0xFFFFFFFF)
        self.assertFalse(control["mismatch"]["event_observation_match"])
        self.assertFalse(control["mismatch"]["memory_match"])


if __name__ == "__main__":
    unittest.main()
