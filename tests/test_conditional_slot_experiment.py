import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.conditional_slot_experiment import (
    CALLER_WINDOWS, FUNCTIONS, ROOT, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestConditionalSlotExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )
        cls.image, cls.game_info, cls.ledger = (
            pinned.image, pinned.game_info, pinned.ledger
        )

    def test_instruction_shapes_and_direct_callers_are_pinned(self):
        reference = verify_reference(self.image, self.game_info, self.ledger)
        self.assertEqual(set(int(address, 16) for address in reference["functions"]),
                         set(FUNCTIONS))
        self.assertEqual(len(reference["caller_windows"]), len(CALLER_WINDOWS))
        self.assertEqual(len(reference["callers"]["0x14e744"]), 2)
        self.assertEqual(len(reference["callers"]["0x2b0418"]), 4)

    def test_hash_and_instruction_drift_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, {**self.game_info, "code_sha256": "0" * 64},
                             self.ledger)
        changed = bytearray(self.image)
        changed[0x0014E744 - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Original instruction sequence changed"):
            verify_reference(bytes(changed),
                             {**self.game_info,
                              "code_sha256": hashlib.sha256(changed).hexdigest()},
                             self.ledger)

    def test_candidates_callers_and_controls_on_two_seeds(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                              samples=1, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["function_comparisons"], 14)
            self.assertTrue(all(item["passed"] for item in report["functions"]))
            self.assertEqual(len(report["caller_results"]), 8)
            self.assertTrue(all(item["passed"] for item in report["caller_results"]))
            self.assertEqual(len(report["negative_controls"]), 2)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
