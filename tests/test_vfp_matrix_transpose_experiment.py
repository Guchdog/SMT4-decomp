from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.semantic_experiment_support import load_pinned_reference
from tools.vfp_matrix_transpose_experiment import FUNCTIONS, ROOT, run, verify_reference


class VfpMatrixTransposeExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv")
        cls.image, cls.game_info, cls.ledger = pinned.image, pinned.game_info, pinned.ledger

    def test_pinned_bodies_and_aapcs_compatibility(self):
        report = verify_reference(self.image, self.game_info["code_sha256"], self.ledger)
        self.assertEqual(set(map(lambda x: int(x, 16), report["functions"])), set(FUNCTIONS))
        self.assertEqual({item["size"] for item in report["functions"].values()}, {76})
        self.assertTrue(all("AAPCS core registers r0-r2" in item["abi_evidence"]
                            for item in report["functions"].values()))
        with self.assertRaises(ValueError):
            changed = bytearray(self.image)
            changed[0x0023AFF0 - 0x00100000] ^= 1
            verify_reference(bytes(changed), self.game_info["code_sha256"], self.ledger)

    def test_two_seed_differential_runs_and_negative_controls(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory(prefix="vfp-matrix-transpose-") as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary), seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["function_comparisons"], 128)
            self.assertEqual(report["cases_per_function"], 64)
            self.assertEqual(len(report["functions"]), 2)
            self.assertTrue(all(item["passed"] for item in report["functions"]))
            self.assertEqual({item["candidate_bytes"] for item in report["functions"]}, {168})
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
            self.assertEqual(report["seed"], seed)
            self.assertFalse(report["fast_math"])


if __name__ == "__main__":
    unittest.main()
