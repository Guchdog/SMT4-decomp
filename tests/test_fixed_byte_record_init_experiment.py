import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.fixed_byte_record_init_experiment import (
    FUNCTIONS, ROOT, SEEDS, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestFixedByteRecordInitExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(ROOT / "extracted/exefs/code.bin",
                                       ROOT / "config/game_info.json",
                                       ROOT / "config/functions.csv")
        cls.image, cls.game_info, cls.ledger = pinned.image, pinned.game_info, pinned.ledger

    def test_reference_bodies_and_hash_pin(self):
        report = verify_reference(self.image, self.game_info, self.ledger)
        self.assertEqual({int(x, 16) for x in report["functions"]}, set(FUNCTIONS))
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, {**self.game_info, "code_sha256": "0" * 64}, self.ledger)
        changed = bytearray(self.image)
        changed[next(iter(FUNCTIONS)) - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "instruction sequence changed"):
            verify_reference(bytes(changed),
                             {**self.game_info,
                              "code_sha256": hashlib.sha256(changed).hexdigest()}, self.ledger)

    def test_pair_on_two_seeds_with_late_faults_and_controls(self):
        for seed in SEEDS:
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary), seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["function_comparisons"], 2 * report["cases_per_function"])
            self.assertEqual(len(report["functions"]), 2)
            self.assertTrue(all(row["passed"] for row in report["functions"]))
            self.assertEqual(report["cases_per_function"], 75)
            self.assertTrue(all(row["fault_cases"] == 3 for row in report["functions"]))
            self.assertEqual(len(report["negative_controls"]), 2)
            self.assertTrue(all(control["detected"] for control in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
