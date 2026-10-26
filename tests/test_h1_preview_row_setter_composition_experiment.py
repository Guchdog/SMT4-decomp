"""Assertions for the private helper-plus-row-setter composition report."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "build/agent-work/H1-semantic/h1-preview-row-setter-composition/overnight-20261025-row-setter-composition/results-v4/report.json"


class PreviewRowSetterCompositionReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_all_composition_cases_pass_and_cover_both_setter_sites(self):
        report = self.report
        self.assertEqual(report["case_count"], 8)
        self.assertTrue(report["passed"])
        self.assertTrue(all(case["passed"] for case in report["cases"]))
        by_name = {case["name"]: case for case in report["cases"]}
        self.assertFalse(by_name["endpoint disabled sequence skips setter"]["original"]["setter_calls"])
        for name in ("endpoint restart marker calls pinned setter site one",
                     "endpoint ordinary next calls pinned setter site two"):
            case = by_name[name]
            self.assertEqual(len(case["original"]["setter_calls"]), 1)
            self.assertEqual(len(case["candidate"]["setter_calls"]), 1)
            self.assertEqual(case["original"]["setter_calls"][0]["args"],
                             case["candidate"]["setter_calls"][0]["args"])

    def test_projection_records_stubs_and_setter_negative_control(self):
        report = self.report
        self.assertEqual(report["negative_control"]["name"],
                         "missing_setter_animation_index_store")
        self.assertTrue(report["negative_control"]["detected"])
        self.assertIn("object/table/sequence memory differs",
                      report["negative_control"]["errors"])
        self.assertEqual(set(report["stub_contracts"]),
                         {"interpolation", "tail_a_0x002b1fc0",
                          "translation_track_0x002b1dfc", "tail_c_0x002b1c8c"})
        self.assertEqual(report["evidence"]["runtime"], "not_run")


if __name__ == "__main__":
    unittest.main()
