from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.semantic_experiment_support import load_pinned_reference
from tools.vfp_ui_transpose_experiment import ADDRESS, ROOT, run, verify_reference


class VfpUiTransposeExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv")
        cls.image, cls.info, cls.ledger = pinned.image, pinned.game_info, pinned.ledger

    def test_pinned_body_and_aapcs_contract(self):
        report = verify_reference(self.image, self.info["code_sha256"], self.ledger)
        self.assertEqual(int(report["address"], 16), ADDRESS)
        self.assertEqual(report["size"], 72)
        self.assertIn("caller-saved s0-s15", report["abi_evidence"])
        self.assertIn("No direct ARM BL callers", report["caller_evidence"])
        with self.assertRaises(ValueError):
            mutated = bytearray(self.image)
            mutated[ADDRESS - 0x00100000] ^= 1
            verify_reference(bytes(mutated), self.info["code_sha256"], self.ledger)

    def test_two_seed_differential_and_control(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory(prefix="vfp-ui-transpose-") as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary), seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["function_comparisons"], 64)
            self.assertTrue(report["negative_control"]["detects_transpose_order"])
            self.assertFalse(report["fast_math"])


if __name__ == "__main__":
    unittest.main()
