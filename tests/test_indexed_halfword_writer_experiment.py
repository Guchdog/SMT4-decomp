import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.indexed_halfword_writer_experiment import (
    EXPECTED_INSTRUCTIONS, FUNCTIONS, ROOT, _direct_arm_bl_callers,
    make_alias_cases, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestIndexedHalfwordWriterReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )
        cls.image, cls.game, cls.ledger = pinned.image, pinned.game_info, pinned.ledger

    def test_instruction_words_and_direct_arm_bl_callers_are_pinned(self):
        report = verify_reference(self.image, self.game, self.ledger)
        self.assertEqual(set(int(address, 16) for address in report["functions"]),
                         set(FUNCTIONS))
        self.assertEqual(report["direct_arm_bl_callers"]["0x35bbc4"], ["0x35b56c"])
        self.assertEqual(report["direct_arm_bl_callers"]["0x35c00c"], [])
        for item in report["functions"].values():
            self.assertEqual(len(item["instructions"]), len(EXPECTED_INSTRUCTIONS))
            self.assertEqual(item["ordered_effects"][0],
                             "load *r1; clear one byte at first_target+8")

    def test_rehashed_instruction_mutation_is_rejected(self):
        changed = bytearray(self.image)
        changed[0x0035BBC4 - 0x00100000] ^= 1
        altered_game = {**self.game, "code_sha256": hashlib.sha256(changed).hexdigest()}
        with self.assertRaisesRegex(ValueError, "Pinned instruction sequence changed"):
            verify_reference(bytes(changed), altered_game, self.ledger)

    def test_alias_fixtures_pin_the_order_sensitive_cases(self):
        cases = make_alias_cases(7)
        self.assertEqual([case.label for case in cases], [
            "alias-clear-mutates-pointer-slot",
            "alias-clear-mutates-base-before-ldrd",
            "alias-halfword-overwrites-index-before-increment",
        ])


class TestIndexedHalfwordWriterExperiment(unittest.TestCase):
    def test_two_seed_differential_runs_controls_and_faults(self):
        for seed in (20261024, 7):
            with tempfile.TemporaryDirectory(prefix=f"smt4-indexed-halfword-{seed}-") as temp:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temp), seed, samples=16)
                disk_report = json.loads((Path(temp) / "report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"], seed)
            self.assertTrue(disk_report["passed"])
            self.assertEqual(len(report["functions"]), 2)
            self.assertTrue(all(item["passed"] and item["cases"] == 27
                                for item in report["functions"]))
            for item in report["functions"]:
                self.assertTrue(item["ordered_trace_matches_candidate"])
                self.assertEqual(
                    [(event["operation"], event["data_offset"], event["width_bytes"])
                     for event in item["ordered_access_trace"]],
                    [("read", "0x80", 4), ("write", "0x308", 1),
                     ("read", "0x20c", 4), ("read", "0x210", 4),
                     ("read", "0x80", 4), ("read", "0x600", 2),
                     ("write", "0x30a", 2), ("read", "0x210", 4),
                     ("write", "0x210", 4)],
                )
            self.assertEqual(len(report["negative_controls"]), 6)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
            self.assertEqual(len(report["fault_probes"]), 4)
            self.assertTrue(all(item["passed"] for item in report["fault_probes"]))
            self.assertTrue(all(item["original_fault"] for item in report["fault_probes"]))
            self.assertEqual(len(report["caller_results"]), 1)
            self.assertTrue(report["caller_results"][0]["passed"])
            self.assertEqual(report["caller_results"][0]["original_continuation"], "0x35b578")
            self.assertEqual(report["reference"]["direct_arm_bl_callers"]["0x35bbc4"],
                             ["0x35b56c"])
            self.assertEqual(report["reference"]["direct_arm_bl_callers"]["0x35c00c"], [])


if __name__ == "__main__":
    unittest.main()
