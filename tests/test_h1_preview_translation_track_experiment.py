from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPORT = (ROOT / "build/agent-work/H1-semantic/h1-preview-translation-track-candidate/"
          "overnight-20261025-translation-track/run-04/report.json")


class PreviewTranslationTrackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not REPORT.is_file():
            raise AssertionError("run tools/h1_preview_translation_track_experiment.py first")
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_all_pinned_arm_fixtures_match(self):
        self.assertTrue(self.report["passed"])
        self.assertEqual(self.report["case_count"], 17)
        self.assertTrue(all(case["passed"] for case in self.report["cases"]))
        self.assertIsNone(self.report["first_mismatch"])

    def test_endpoint_interpolation_and_sequence_paths_are_present(self):
        names = {case["name"] for case in self.report["cases"]}
        for name in (
            "disabled completion gate returns unchanged",
            "null translation table returns unchanged",
            "mode zero direction zero endpoint",
            "mode zero direction one endpoint",
            "mode nonzero direction zero endpoint",
            "mode nonzero direction one endpoint",
            "interpolation direction one reversed delta",
            "duration equals progress selects endpoint",
            "duration one above progress interpolates",
            "sequence disabled marks complete",
            "sequence enabled null pointer marks complete",
            "sequence current minus one sentinel",
            "sequence next minus three sentinel",
            "sequence next minus two restarts index",
            "sequence ordinary next updates index and animation",
        ):
            self.assertIn(name, names)

    def test_wrong_neighbor_offset_negative_control_is_detected(self):
        control = self.report["negative_controls"][0]
        self.assertEqual(control["name"], "wrong_common_tail_neighbor_offset")
        self.assertTrue(control["detected"])
        self.assertIn("object/table/sequence memory differs", control["errors"])

    def test_vfp_diagnostics_and_stub_free_scope_are_explicit(self):
        self.assertIn("vfp_scratch_s0_s3", self.report["cases"][6]["original"])
        self.assertIn("no external callees", " ".join(self.report["limits"]))


if __name__ == "__main__":
    unittest.main()
