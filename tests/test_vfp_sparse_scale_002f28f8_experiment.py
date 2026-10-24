import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.semantic_experiment_support import load_pinned_reference
from tools.vfp_sparse_scale_002f28f8_experiment import (
    ADDRESS, ROOT, run, verify_reference,
)


class TestVfpSparseScale002f28f8Experiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv")
        cls.image, cls.game_info, cls.ledger = pinned.image, pinned.game_info, pinned.ledger

    def test_reference_body_and_hash_pin(self):
        report = verify_reference(self.image, self.game_info, self.ledger)
        self.assertEqual(set(map(lambda x: int(x, 16), report["functions"])), {ADDRESS})
        self.assertEqual(report["functions"][hex(ADDRESS)]["size"], 68)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, {**self.game_info, "code_sha256": "0" * 64}, self.ledger)
        changed = bytearray(self.image)
        changed[ADDRESS - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "reference body changed"):
            verify_reference(bytes(changed),
                             {**self.game_info, "code_sha256": hashlib.sha256(changed).hexdigest()},
                             self.ledger)

    def test_two_seed_differential_and_negative_controls(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary), seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["function_comparisons"], report["cases_per_function"])
            self.assertEqual(report["cases_per_function"], 388)
            function = report["functions"][0]
            self.assertTrue(function["passed"])
            self.assertNotEqual(function["candidate_bytes"], 68)
            self.assertTrue(function["late_fault_evidence"]["reference_faulted"])
            self.assertTrue(function["late_fault_evidence"]["candidate_faulted"])
            self.assertTrue(function["late_fault_evidence"]["ordinary_memory_and_access_sets_equal"])
            self.assertEqual(len(report["negative_controls"]), 2)
            self.assertTrue(all(control["detected"] for control in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
