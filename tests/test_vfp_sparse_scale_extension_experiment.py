import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.semantic_experiment_support import load_pinned_reference
from tools.vfp_sparse_scale_experiment import FUNCTIONS as PARENT_FUNCTIONS
from tools.vfp_sparse_scale_extension_experiment import (
    FUNCTIONS, ROOT, SIZES, run, verify_reference,
)


class TestVfpSparseScaleExtensionExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv")
        cls.image, cls.game_info, cls.ledger = pinned.image, pinned.game_info, pinned.ledger

    def test_eight_distinct_new_addresses_and_pinned_lane_maps(self):
        self.assertEqual(len(FUNCTIONS), 8)
        self.assertFalse(set(FUNCTIONS) & set(PARENT_FUNCTIONS))
        report = verify_reference(self.image, self.game_info, self.ledger)
        self.assertEqual({int(address, 16) for address in report["functions"]}, set(FUNCTIONS))
        self.assertEqual({item["size"] for item in report["functions"].values()}, {104, 116})
        self.assertTrue(all(item["ordered_lane_offsets"] for item in report["functions"].values()))
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, {**self.game_info, "code_sha256": "0" * 64}, self.ledger)
        changed = bytearray(self.image)
        changed[next(iter(FUNCTIONS)) - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "reference body changed"):
            verify_reference(bytes(changed),
                             {**self.game_info, "code_sha256": hashlib.sha256(changed).hexdigest()},
                             self.ledger)

    def test_two_seed_differential_reports_faults_and_negative_controls(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / f"extension-seed-{seed}"
                report = run(ROOT / "extracted/exefs/code.bin", output, seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["function_comparisons"], 8 * report["cases_per_function"])
            self.assertEqual(len(report["reference_functions"]), 8)
            self.assertTrue(all(item["passed"] for item in report["functions"]))
            self.assertTrue(all(
                item["late_fault_evidence"]["reference_faulted"]
                and item["late_fault_evidence"]["candidate_faulted"]
                and item["late_fault_evidence"]["ordinary_memory_and_access_sets_equal"]
                for item in report["functions"]))
            self.assertEqual(len(report["negative_controls"]), 2)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
