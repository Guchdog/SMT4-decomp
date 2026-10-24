import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.indexed_word_vector_00151ff4_experiment import (
    ADDRESS, CALLER, EXPECTED_WORDS, ROOT, _direct_arm_bl_callers, run,
    verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestIndexedWordVectorReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )
        cls.image, cls.game, cls.ledger = pinned.image, pinned.game_info, pinned.ledger

    def test_instruction_boundary_and_direct_arm_caller_are_pinned(self):
        report = verify_reference(self.image, self.game, self.ledger)
        self.assertEqual(report["function_size"], 96)
        self.assertEqual([int(word, 16) for word in report["instruction_words"]],
                         list(EXPECTED_WORDS))
        self.assertEqual(report["direct_arm_bl_callers"], [hex(CALLER["callsite"])])
        self.assertEqual(report["caller_argument_setup_words"], ["0xe2841004", "0xe1a00005"])
        self.assertEqual(report["caller_continuation_words"], ["0xe3a00001", "0xe8bd8070"])
        self.assertEqual(_direct_arm_bl_callers(self.image), [CALLER["callsite"]])

    def test_instruction_or_revision_mutation_is_rejected(self):
        changed = bytearray(self.image)
        changed[ADDRESS - 0x00100000] ^= 1
        altered_game = {**self.game, "code_sha256": hashlib.sha256(changed).hexdigest()}
        with self.assertRaisesRegex(ValueError, "Pinned instruction sequence changed"):
            verify_reference(bytes(changed), altered_game, self.ledger)


class TestIndexedWordVectorExperiment(unittest.TestCase):
    def test_two_seed_differential_alias_fault_caller_and_controls(self):
        for seed in (20261024, 7):
            with tempfile.TemporaryDirectory(prefix=f"smt4-indexed-vector-{seed}-") as temp:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temp), seed, samples=16)
                saved = json.loads((Path(temp) / "report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"], seed)
            self.assertTrue(saved["passed"], seed)
            self.assertEqual(len(report["cases"]), 28)
            self.assertTrue(all(case["passed"] for case in report["cases"]))
            self.assertTrue(all(control["detected"] for control in report["negative_controls"]))
            self.assertTrue(report["fault_probe"]["passed"])
            self.assertEqual(report["fault_probe"]["original_writes"], 4)
            self.assertEqual(report["fault_probe"]["candidate_writes"], 4)
            self.assertTrue(report["caller_window"]["passed"])
            self.assertFalse(report["candidate"]["same_bytes_as_original"])
            self.assertEqual(report["reference"]["direct_arm_bl_callers"], ["0x14d4b4"])


if __name__ == "__main__":
    unittest.main()
