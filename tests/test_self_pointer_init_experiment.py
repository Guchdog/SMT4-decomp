import tempfile
import unittest
from pathlib import Path

from tools.self_pointer_init_experiment import (
    EXPECTED_BYTES, EXPECTED_WRITES, ROOT, TARGETS, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestSelfPointerInitializerExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )

    def test_pinned_bytes_and_identical_pair(self):
        rows = verify_reference(self.pinned.image, self.pinned.ledger)
        self.assertEqual(TARGETS, (0x00237F10, 0x003F7394))
        self.assertEqual(EXPECTED_WRITES, ((0, 4, 0), (4, 1, 1), (8, 4, "self+8"),
                                           (0x10, 4, 0), (0x0C, 4, "self+8")))
        self.assertEqual(self.pinned.image[0x00237F10 - 0x00100000:
                                           0x00237F10 - 0x00100000 + 36], EXPECTED_BYTES)
        self.assertEqual(rows[0x00237F10]["category"], rows[0x003F7394]["category"])

    def test_two_seed_function_fault_and_negative_evidence(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                             samples=2, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["function_comparisons"], 12)
            self.assertEqual([item["cases"] for item in report["functions"]], [6, 6])
            self.assertEqual(report["direct_caller_windows"], [])
            self.assertEqual(len(report["ordered_write_fault_cases"]), 2)
            self.assertTrue(all(item["passed"] and item["completed_writes_before_fault"] == 3
                                and item["write_attempts_including_fault"] == 4
                                for item in report["ordered_write_fault_cases"]))
            self.assertEqual(len(report["negative_controls"]), 8)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
