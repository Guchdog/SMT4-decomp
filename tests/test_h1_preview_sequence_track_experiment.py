"""Focused assertions for the private 0x002B1C8C ARM differential report."""
import json
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = Path(os.environ.get(
    "H1_SEQUENCE_TRACK_REPORT",
    ROOT / "build/agent-work/H1-semantic/h1-preview-sequence-track-candidate/"
    "overnight-20261025-sequence-track/run-01/report.json"))


class PreviewSequenceTrackExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not REPORT.is_file():
            raise AssertionError(f"run the private experiment first: {REPORT}")
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_name = {case["name"]: case for case in cls.report["cases"]}

    def test_identity_and_complete_matrix(self):
        self.assertEqual(self.report["entry"], "0x2b1c8c")
        self.assertEqual(self.report["size"], 368)
        self.assertEqual(self.report["exit"], "0x2b1dfc")
        self.assertTrue(self.report["passed"])
        self.assertGreaterEqual(self.report["case_count"], 20)
        self.assertTrue(all(case["passed"] for case in self.report["cases"]))

    def test_distinct_track_and_sequence_sentinel_semantics(self):
        ordinary_case = self.by_name["next ordinary track writes return object plus four"]
        self.assertEqual(ordinary_case["original"]["r0"], 0x01E01004)
        ordinary_minus_three = bytes.fromhex(self.by_name[
            "next row minus three is ordinary track value"]["original"]["object"])
        self.assertEqual(int.from_bytes(ordinary_minus_three[4:8], "little", signed=True), -3)
        sequence_minus_two = self.by_name["next sequence minus two is an unmatched lookup ID"]
        obj = bytes.fromhex(sequence_minus_two["original"]["object"])
        self.assertEqual(int.from_bytes(obj[0x70:0x74], "little"), 0)
        self.assertEqual(obj[0x89], 0)
        self.assertEqual(sequence_minus_two["original"]["r0"], 0x01E01000)

    def test_lookup_transition_returns_interior_object_pointer(self):
        selected = self.by_name["sequence target one selects after one sentinel"]
        self.assertEqual(selected["original"]["r0"], 0x01E01004)
        ended = self.by_name["next sequence minus three completes"]
        self.assertEqual(ended["original"]["r0"], 0x01E01000)

    def test_lookup_count_sentinel_ordinal_and_signed_index_edges(self):
        selected = bytes.fromhex(self.by_name[
            "sequence target one selects after one sentinel"]["original"]["object"])
        self.assertNotEqual(int.from_bytes(selected[0x70:0x74], "little"), 0)
        self.assertEqual(int.from_bytes(selected[4:8], "little", signed=True), 40)
        self.assertEqual(int.from_bytes(selected[8:12], "little", signed=True), -1)
        for name in ("sequence target ordinal not present clears handle",
                     "zero lookup count clears handle"):
            result = bytes.fromhex(self.by_name[name]["original"]["object"])
            self.assertEqual(int.from_bytes(result[0x70:0x74], "little"), 0)
        wrapped = bytes.fromhex(self.by_name[
            "sequence index maximum wraps to signed minimum"]["original"]["object"])
        self.assertEqual(int.from_bytes(wrapped[0x82:0x84], "little", signed=True), -0x8000)

    def test_wrong_duration_offset_is_detected(self):
        control = self.report["negative_control"]
        self.assertTrue(control["detected"])
        self.assertIn("r0 differs", control["errors"])
        self.assertIn("mapped object/lookup/sequence memory differs", control["errors"])
        original = bytes.fromhex(control["case"]["original"]["object"])
        mutant = bytes.fromhex(control["case"]["candidate"]["object"])
        self.assertNotEqual(original[0x74:0x78], mutant[0x74:0x78])


if __name__ == "__main__":
    unittest.main()
