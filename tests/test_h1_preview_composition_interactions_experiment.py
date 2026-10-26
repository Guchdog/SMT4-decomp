"""Focused checks for maximal reachable preview-helper composition paths."""
from __future__ import annotations

import json
import os
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPORT = Path(os.environ.get(
    "H1_PREVIEW_INTERACTIONS_REPORT",
    ROOT / "build/agent-work/H1-semantic/h1-preview-composition-interactions/"
    "overnight-20261025-preview-interactions/run-02/report.json"))


class PreviewCompositionInteractionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not REPORT.is_file():
            raise AssertionError(f"run the private experiment first: {REPORT}")
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_name = {case["name"]: case for case in cls.report["cases"]}

    def test_three_joint_paths_cover_the_reachable_maxima(self):
        self.assertTrue(self.report["passed"])
        self.assertEqual(self.report["case_count"], 3)
        self.assertTrue(all(case["passed"] for case in self.report["cases"]))
        expected = self.report["expected_call_names"]
        observed = self.report["observed_call_names"]
        self.assertEqual(observed, expected)
        self.assertEqual(expected[
            "helper interpolation + scale endpoint + translation endpoint + selector row advance"],
            ["divide", "divide", "scale", "translation", "selector"])
        self.assertEqual(expected[
            "helper setter + scale interpolation + translation interpolation + selector row advance"],
            ["setter", "scale", "translation", "selector"])
        self.assertEqual(expected[
            "helper + scale + translation interpolation with selector sequence selection"],
            ["divide", "divide", "scale", "translation", "selector"])

    def test_helper_divide_and_setter_arms_are_not_claimed_together(self):
        gates = self.report["gate_analysis"]
        self.assertIn("Mutually exclusive", gates["helper_interpolation_vs_setter"])
        self.assertEqual(len(gates["maximum_reachable_sets"]), 2)
        divide_case = self.by_name[
            "helper interpolation + scale endpoint + translation endpoint + selector row advance"]
        setter_case = self.by_name[
            "helper setter + scale interpolation + translation interpolation + selector row advance"]
        divide_names = [call["name"] for call in divide_case["original"]["calls"]]
        setter_names = [call["name"] for call in setter_case["original"]["calls"]]
        self.assertIn("divide", divide_names)
        self.assertNotIn("setter", divide_names)
        self.assertIn("setter", setter_names)
        self.assertNotIn("divide", setter_names)

    def test_joint_fixture_effects_and_targeted_mutation(self):
        endpoint_case = self.by_name[
            "helper interpolation + scale endpoint + translation endpoint + selector row advance"]
        obj = bytes.fromhex(endpoint_case["original"]["object_after_hex"])
        self.assertEqual(struct.unpack_from("<f", obj, 0x20)[0], 5.0)
        self.assertEqual(struct.unpack_from("<f", obj, 0x24)[0], 6.0)
        self.assertEqual(struct.unpack_from("<i", obj, 4)[0], 3)

        setter_case = self.by_name[
            "helper setter + scale interpolation + translation interpolation + selector row advance"]
        obj = bytes.fromhex(setter_case["original"]["object_after_hex"])
        self.assertEqual(struct.unpack_from("<h", obj, 0x50)[0], 2)

        sequence_case = self.by_name[
            "helper + scale + translation interpolation with selector sequence selection"]
        obj = bytes.fromhex(sequence_case["original"]["object_after_hex"])
        self.assertEqual(struct.unpack_from("<i", obj, 4)[0], 42)
        self.assertNotEqual(struct.unpack_from("<I", obj, 0x70)[0], 0)

        control = self.report["negative_control"]
        self.assertTrue(control["detected"])
        mismatch = control["case"]["first_memory_mismatch"]
        self.assertEqual(mismatch["address"], "0x2000050")
        self.assertEqual((mismatch["original"], mismatch["candidate"]), (2, 0))

    def test_partial_evidence_limits_are_preserved(self):
        self.assertEqual(self.report["evidence"]["runtime"], "not_run")
        self.assertEqual(self.report["evidence"]["arm_differential"],
                         "partial_synthetic_joint_paths")
        self.assertTrue(any("non-aliasing" in item for item in self.report["limitations"]))
        self.assertTrue(any("mutually exclusive" in item for item in self.report["limitations"]))


if __name__ == "__main__":
    unittest.main()
