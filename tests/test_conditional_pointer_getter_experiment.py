import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.conditional_pointer_getter_experiment import (
    CALLER_WINDOW, FUNCTIONS, ROOT, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestConditionalPointerGetterExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )
        cls.image, cls.game_info, cls.ledger = pinned.image, pinned.game_info, pinned.ledger

    def test_instruction_shapes_callers_and_manual_window_are_pinned(self):
        reference = verify_reference(self.image, self.game_info, self.ledger)
        self.assertEqual(set(int(address, 16) for address in reference["functions"]),
                         set(FUNCTIONS))
        self.assertEqual(len(reference["callers"]["0x240ea4"]), 18)
        self.assertEqual(len(reference["callers"]["0x29e3bc"]), 25)
        self.assertEqual(reference["caller_window"]["start"], hex(CALLER_WINDOW["start"]))
        self.assertEqual(len(reference["caller_window"]["calls"]), 2)

    def test_hash_and_function_drift_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, {**self.game_info, "code_sha256": "0" * 64},
                             self.ledger)
        changed = bytearray(self.image)
        changed[0x00240EA4 - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Original instruction sequence changed"):
            verify_reference(bytes(changed),
                             {**self.game_info,
                              "code_sha256": hashlib.sha256(changed).hexdigest()},
                             self.ledger)

    def test_candidates_callers_and_negative_controls_on_two_seeds(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                             samples=2, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["function_comparisons"], 534)
            self.assertEqual(report["caller_comparisons"], 8)
            self.assertEqual(len(report["unmapped_slot_fault_results"]), 4)
            self.assertTrue(all(item["passed"]
                                for item in report["unmapped_slot_fault_results"]))
            self.assertTrue(all(item["passed"] for item in report["functions"]))
            self.assertTrue(all(item["passed"] for item in report["caller_results"]))
            self.assertEqual(len(report["negative_controls"]), 3)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
            for item in report["functions"]:
                self.assertEqual(item["candidate_bytes"], 24)
                self.assertEqual(item["candidate_instructions"][0], "ldrb r2, [r0, #0x62]")
                self.assertTrue(any(ins.startswith("ldreq r0, [r1,")
                                    for ins in item["candidate_instructions"]))
                self.assertEqual(item["candidate_instructions"][-1], "bx lr")
            width = next(item for item in report["negative_controls"]
                         if item["name"] == "negative_wrong_flag_width")
            self.assertIn("read footprint", width["reason"])


if __name__ == "__main__":
    unittest.main()
