import tempfile
import unittest
from pathlib import Path

from tools.title_touch_family_experiment import (
    EXPECTED_SHA256, ROOT, TOUCH_START, TOUCH_STOP, run, verify_image,
)


class TestTitleTouchFamilyExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()

    def test_reference_image_and_touch_window_are_pinned(self):
        evidence = verify_image(self.image)
        self.assertEqual(evidence["sha256"], EXPECTED_SHA256)
        self.assertEqual(evidence["start"], "0x1e9e4c")
        self.assertEqual(evidence["stop"], "0x1e9eb8")

    def test_reference_hash_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_image(self.image + b"changed")

    def test_touch_family_matches_exhaustive_stable_state_vectors(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run(ROOT / "extracted/exefs/code.bin", Path(directory))
        self.assertTrue(report["passed"])
        self.assertEqual(report["state_vector_count"], 6 ** 4)
        self.assertEqual(report["comparison_count"], 2 * 6 ** 4)
        self.assertEqual(report["passed_comparisons"], report["comparison_count"])
        self.assertTrue(all(case["semantic_assertion_passed"]
                            for case in report["priority_cases"]))
        by_name = {case["case"]: case for case in report["priority_cases"]}
        self.assertEqual(by_name["priority-first-selection-match-wins"]["original"]["cursor"], 0)
        self.assertEqual(by_name["priority-last-confirm-match-wins"]["original"]["cursor"], 3)
        self.assertEqual(by_name["priority-confirm-overrides-earlier-selection"]["original"]["cursor"], 2)
        self.assertEqual(by_name["priority-confirm-is-sticky-if-no-state-6"]["original"]["confirm"], 1)
        self.assertEqual(TOUCH_START, 0x001E9E4C)
        self.assertEqual(TOUCH_STOP, 0x001E9EB8)


if __name__ == "__main__":
    unittest.main()
