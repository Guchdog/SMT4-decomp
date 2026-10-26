"""Focused checks over the completed private 0x002B1FC0 differential report."""
import json
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = (ROOT / "build/agent-work/H1-semantic/h1-preview-scale-track-candidate/"
          "overnight-20261025-scale-track/run-04/report.json")


class PreviewScaleTrackExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not REPORT.is_file():
            raise AssertionError("run tools/h1_preview_scale_track_experiment.py first")
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_identity_and_all_directed_cases(self):
        self.assertEqual(self.report["entry"], "0x2b1fc0")
        self.assertEqual(self.report["size"], 444)
        self.assertEqual(self.report["exit"], "0x2b217c")
        self.assertTrue(self.report["passed"])
        self.assertEqual(self.report["case_count"], 22)
        self.assertTrue(all(case["passed"] for case in self.report["cases"]))

    def test_track_gate_endpoint_and_interpolation_boundaries(self):
        names = {case["name"] for case in self.report["cases"]}
        self.assertIn("gate byte already complete", names)
        self.assertIn("null scale-track table returns", names)
        self.assertIn("endpoint mode nonzero direction zero", names)
        self.assertIn("endpoint mode nonzero direction nonzero", names)
        self.assertIn("endpoint row-mode zero direction nonzero selects opposite endpoint", names)
        self.assertIn("interpolation direction zero duration eight", names)
        self.assertIn("interpolation direction nonzero duration eight", names)
        self.assertIn("progress maximum increments with halfword wrap", names)
        self.assertIn("negative progress with zero duration exercises VFP divide by zero", names)

    def test_signed_sequence_markers_and_track_transition(self):
        by_name = {case["name"]: case for case in self.report["cases"]}
        for name in ("current sequence end marker sets completion",
                     "next sequence minus one marker sets completion",
                     "next sequence minus three marker sets completion"):
            obj = bytes.fromhex(by_name[name]["original"]["object"])
            self.assertEqual(obj[0x87], 1)
        transitioned = bytes.fromhex(by_name[
            "ordinary sequence entry selects row and signed direction"]["original"]["object"])
        self.assertEqual(struct.unpack_from("<h", transitioned, 0x5C)[0], 1)
        self.assertEqual(transitioned[0x60], 0xFF)
        self.assertEqual(struct.unpack_from("<h", transitioned, 0x7E)[0], 1)

    def test_vfp_status_and_negative_control(self):
        by_name = {case["name"]: case for case in self.report["cases"]}
        divzero = by_name["negative progress with zero duration exercises VFP divide by zero"]
        self.assertEqual(divzero["original"]["state"]["fpscr"],
                         divzero["candidate"]["state"]["fpscr"])
        self.assertNotEqual(divzero["original"]["state"]["fpscr"] & 0x2, 0)
        control = self.report["negative_control"]
        self.assertEqual(control["name"], "missing_selected_sequence_scale_clear")
        self.assertTrue(control["detected"])


if __name__ == "__main__":
    unittest.main()
