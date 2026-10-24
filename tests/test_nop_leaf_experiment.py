import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.nop_leaf_experiment import (
    ADDRESSES, ROOT, SEEDS, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestNopLeafExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )
        cls.image, cls.game_info, cls.ledger = (
            pinned.image, pinned.game_info, pinned.ledger
        )

    def test_instruction_bytes_and_sizes_are_pinned(self):
        reference = verify_reference(self.image, self.game_info, self.ledger)
        self.assertEqual(set(map(lambda value: int(value, 16), reference["functions"])),
                         set(ADDRESSES))
        for item in reference["functions"].values():
            self.assertEqual(item["size"], 8)
            self.assertEqual(item["instructions"], ["mov r0, r0", "bx lr"])
            self.assertEqual(item["original_bytes_hex"], "0000a0e11eff2fe1")

    def test_image_and_instruction_drift_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, {**self.game_info, "code_sha256": "0" * 64},
                             self.ledger)
        changed = bytearray(self.image)
        changed[ADDRESSES[0] - 0x00100000] ^= 1
        changed_info = {**self.game_info,
                        "code_sha256": hashlib.sha256(changed).hexdigest()}
        with self.assertRaisesRegex(ValueError, "instruction sequence changed"):
            verify_reference(bytes(changed), changed_info, self.ledger)

    def test_candidates_and_targeted_controls_on_two_seeds(self):
        for seed in SEEDS:
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                             samples=64, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["function_comparisons"], 3 * 68)
            self.assertEqual(len(report["functions"]), 3)
            self.assertTrue(all(item["passed"] for item in report["functions"]))
            self.assertEqual(report["caller_windows_executed"], 0)
            self.assertEqual(len(report["negative_controls"]), 4)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
            self.assertEqual({item["state_targeted"] for item in report["negative_controls"]},
                             {"r0", "r1", "nzcv", "memory"})


if __name__ == "__main__":
    unittest.main()
