import tempfile
import unittest
from pathlib import Path

from tools.conditional_mask_copy_003e8ba0_experiment import (
    ROOT, SEEDS, make_cases, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestConditionalMaskCopy003E8BA0(unittest.TestCase):
    def test_reference_and_adjacent_writer_evidence_are_bounded(self):
        reference = load_pinned_reference(ROOT / "extracted/exefs/code.bin",
                                         ROOT / "config/game_info.json",
                                         ROOT / "config/functions.csv")
        evidence = verify_reference(reference)
        self.assertEqual(evidence["size"], 88)
        self.assertEqual(evidence["adjacent_progress_writer"]["address"], "0x003e8b44")
        self.assertIn("adjacent ledger entry only", evidence["adjacent_progress_writer"]["relationship"])

    def test_cases_include_masks_alias_and_two_seed_streams(self):
        for seed in SEEDS:
            cases = list(make_cases(seed, samples=8))
            self.assertEqual(len(cases), 19)
            self.assertEqual(cases[-1].label, "destination-overwrites-mask")
        first = list(make_cases(SEEDS[0], samples=8))
        second = list(make_cases(SEEDS[1], samples=8))
        self.assertNotEqual(first[0].data, second[0].data)

    def test_differential_controls_and_faults_for_two_seeds(self):
        for seed in SEEDS:
            with tempfile.TemporaryDirectory(prefix="smt4-mask-copy-") as directory:
                report = run(ROOT / "extracted/exefs/code.bin", Path(directory), seed=seed, samples=32)
            self.assertTrue(report["passed"], report)
            self.assertEqual(report["comparisons"], 43)
            self.assertTrue(report["negative_control"]["detected"])
            self.assertEqual(len(report["fault_probes"]), 2)
            self.assertTrue(all(item["faults_match"] for item in report["fault_probes"]))


if __name__ == "__main__":
    unittest.main()
