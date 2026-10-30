"""Assertions over the full private H1 preview composition report."""
from __future__ import annotations

import json
import os
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPORT = Path(os.environ.get(
    "H1_PREVIEW_FULL_COMPOSITION_REPORT",
    ROOT / "build/agent-work/H1-semantic/h1-preview-full-composition-fixture-repair/"
    "overnight-20261025-full-composition-fixture-repair/run-01/report.json"))


class PreviewFullCompositionReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_all_six_candidate_components_are_linked_and_matrix_passes(self):
        report = self.report
        self.assertEqual(report["case_count"], 17)
        self.assertTrue(report["passed"])
        self.assertIsNone(report["first_mismatch"])
        self.assertTrue(all(case["passed"] for case in report["cases"]))
        self.assertEqual(report["candidate"]["undefined_symbols"], [])
        self.assertEqual(set(report["candidate"]["sources"]),
                         {"helper", "setter", "divide", "scale", "translation", "selector"})
        observed = {call["name"] for case in report["cases"]
                    for call in case["original"]["calls"]}
        self.assertEqual(observed, {"setter", "divide", "scale", "translation", "selector"})

    def test_fixture_branches_and_dependency_mutation_control(self):
        report = self.report
        names = {case["name"] for case in report["cases"]}
        self.assertIn("null helper pointer early return", names)
        self.assertIn("helper interpolation direction zero uses real divide candidate", names)
        self.assertIn("helper interpolation direction one uses real divide candidate", names)
        self.assertIn("selector track sequence selection updates lookup track", names)
        sequence_case = next(case for case in report["cases"]
                             if case["name"] == "selector track sequence selection updates lookup track")
        selected = bytes.fromhex(sequence_case["original"]["object_after_hex"])
        self.assertEqual(struct.unpack_from("<i", selected, 4)[0], 42)
        self.assertEqual(struct.unpack_from("<I", selected, 0x70)[0], 0x0200E104)
        self.assertEqual(struct.unpack_from("<H", selected, 0x74)[0], 0)
        self.assertEqual(struct.unpack_from("<H", selected, 0x76)[0], 0)
        self.assertEqual(selected[0x89], 0)
        control = report["negative_control"]
        self.assertTrue(control["detected"])
        mismatch = control["case"]["first_memory_mismatch"]
        self.assertEqual(mismatch["address"], "0x2000050")
        self.assertEqual((mismatch["original"], mismatch["candidate"]), (2, 0))
        self.assertEqual(report["evidence"]["runtime"], "not_run")


if __name__ == "__main__":
    unittest.main()
