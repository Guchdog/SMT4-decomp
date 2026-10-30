import tempfile
import unittest
from pathlib import Path

from tools.h1_preview_gate_experiment import (
    EXPECTED_IMAGE, GATE, HELPER, ROOT, run_experiment, verify_reference,
)


class TestH1PreviewGateExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image_path = ROOT / "build/azahar-validation/exefs/code.bin"

    def test_reference_gate_helper_and_caller_are_pinned(self):
        report = verify_reference(self.image_path.read_bytes())
        self.assertEqual(report["sha256"], EXPECTED_IMAGE)
        self.assertEqual(report["gate"]["address"], hex(GATE))
        self.assertEqual(report["gate"]["instruction_count"], 22)
        self.assertEqual(report["helper"]["address"], hex(HELPER))
        self.assertEqual(report["caller"]["formal_arguments"], 0)

    def test_reference_hash_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image_path.read_bytes() + b"changed")

    def test_candidate_matches_branch_matrix_and_boundaries(self):
        output_root = (ROOT / "build/agent-work/H1-semantic/h1-preview-readiness-candidate"
                       / "sleep-20261025-preview-gate/checks/unittest")
        output_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output_root) as directory:
            report = run_experiment(self.image_path, Path(directory))
        self.assertTrue(report["passed"])
        self.assertEqual(report["case_count"], 52)
        self.assertTrue(all(case["passed"] for case in report["cases"]))
        self.assertEqual(len(report["negative_controls"]), 3)
        self.assertTrue(all(control["detected"]
                            for control in report["negative_controls"]))
        self.assertEqual(report["evidence"]["caller"], "partial")
        self.assertEqual(report["evidence"]["runtime"], "not_run")


if __name__ == "__main__":
    unittest.main()
