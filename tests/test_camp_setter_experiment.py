import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.camp_setter_experiment import (
    CALLERS, FUNCTIONS, ROOT, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestCampSetterExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )
        cls.image, cls.game_info, cls.ledger = (
            pinned.image, pinned.game_info, pinned.ledger
        )

    def test_instruction_shapes_and_manual_callers_are_pinned(self):
        reference = verify_reference(self.image, self.game_info, self.ledger)
        self.assertEqual({int(address, 16) for address in reference["functions"]},
                         set(FUNCTIONS))
        self.assertEqual(len(reference["caller_windows"]), 4)
        self.assertEqual(len(reference["direct_callers"]["0x3c8fc8"]), 2)
        self.assertEqual(len(reference["direct_callers"]["0x3c9314"]), 2)
        for evidence in reference["functions"].values():
            self.assertEqual([effect["width_bits"] for effect in evidence["bounded_effects"]],
                             [8, 16, 16])
            self.assertEqual([effect["order"] for effect in evidence["bounded_effects"]],
                             [1, 2, 3])

    def test_hash_and_instruction_drift_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image,
                             {**self.game_info, "code_sha256": "0" * 64},
                             self.ledger)
        changed = bytearray(self.image)
        changed[0x003C8FC8 - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(bytes(changed), self.game_info, self.ledger)
        with self.assertRaisesRegex(ValueError, "Instruction drift"):
            verify_reference(bytes(changed),
                             {**self.game_info,
                              "code_sha256": hashlib.sha256(changed).hexdigest()},
                             self.ledger)

    def test_two_seeds_and_controls(self):
        expected_per_function = 256 + 7 * 7 + 1
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary) / "report",
                             samples=1, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["function_comparisons"],
                             2 * expected_per_function)
            self.assertEqual(len(report["caller_results"]),
                             sum(len(sites) for sites in CALLERS.values()))
            self.assertTrue(all(item["passed"] for item in report["functions"]))
            self.assertTrue(all(item["passed"] for item in report["caller_results"]))
            self.assertEqual(len(report["negative_controls"]), 2)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
