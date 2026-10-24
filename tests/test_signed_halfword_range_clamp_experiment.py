import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.semantic_experiment_support import load_pinned_reference
from tools.signed_halfword_range_clamp_experiment import (
    ADDRESS, ROOT, SEEDS, run, verify_reference,
)


class TestSignedHalfwordRangeClampExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(ROOT / "extracted/exefs/code.bin",
                                       ROOT / "config/game_info.json",
                                       ROOT / "config/functions.csv")
        cls.image, cls.game_info, cls.ledger = pinned.image, pinned.game_info, pinned.ledger

    def test_reference_body_and_hash_pin(self):
        report = verify_reference(self.image, self.game_info, self.ledger)
        self.assertEqual(set(map(lambda x: int(x, 16), report["functions"])), {ADDRESS})
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, {**self.game_info, "code_sha256": "0" * 64}, self.ledger)
        changed = bytearray(self.image)
        changed[ADDRESS - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "instruction sequence changed"):
            verify_reference(bytes(changed),
                             {**self.game_info,
                              "code_sha256": hashlib.sha256(changed).hexdigest()}, self.ledger)

    def test_two_seed_differential_and_targeted_controls(self):
        for seed in SEEDS:
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary), seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["function_comparisons"], 72)
            self.assertTrue(report["functions"][0]["passed"])
            self.assertEqual(len(report["negative_controls"]), 2)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
