import tempfile
import unittest
from pathlib import Path

from tools.h1_touch_caller_experiment import (
    EXPECTED_IMAGE, ROOT, STOP, TOUCH_QUERY, run_experiment, verify_reference,
)


class TestH1TouchCallerExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image_path = ROOT / "build/azahar-validation/exefs/code.bin"

    def test_reference_and_helper_window_are_pinned(self):
        report = verify_reference(self.image_path.read_bytes())
        self.assertEqual(report["sha256"], EXPECTED_IMAGE)
        self.assertEqual(report["address"], "0x1e9e4c")
        self.assertEqual(report["stop"], hex(STOP))
        self.assertEqual(report["helper"], hex(TOUCH_QUERY))
        self.assertEqual(report["instruction_count"], 27)

    def test_reference_hash_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image_path.read_bytes() + b"changed")

    def test_compiled_candidate_matches_directed_caller_cases(self):
        output_root = (ROOT / "build/agent-work/H1-semantic/h1-touch-caller-candidate"
                       / "sleep-20261025-touch-candidate/checks/unittest")
        output_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output_root) as directory:
            report = run_experiment(self.image_path, Path(directory))
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["cases"]), 7)
        self.assertTrue(all(case["passed"] for case in report["cases"]))
        self.assertTrue(all(control["passed"]
                            for control in report["negative_controls"].values()))
        self.assertEqual(report["evidence"]["caller"], "partial")
        self.assertEqual(report["evidence"]["runtime"], "not_run")


if __name__ == "__main__":
    unittest.main()
