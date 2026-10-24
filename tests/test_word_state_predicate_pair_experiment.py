import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tools.semantic_experiment_support import load_pinned_reference
from tools.word_state_predicate_pair_experiment import (
    CALLER_WINDOWS, FUNCTIONS, ROOT, make_cases, verify_reference,
)


class TestWordStatePredicatePairReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv")

    def test_instruction_words_direct_callers_and_branch_windows_are_pinned(self):
        report = verify_reference(self.reference)
        self.assertEqual(set(report["functions"]), {hex(a) for a in FUNCTIONS})
        self.assertEqual(sum(row["direct_call_count"]
                             for row in report["functions"].values()), 4)
        self.assertEqual(set(report["callers"]), {hex(a) for a in CALLER_WINDOWS})

    def test_mutated_reference_instruction_is_rejected(self):
        for address in FUNCTIONS:
            image = bytearray(self.reference.image)
            image[address - 0x00100000] ^= 1
            with self.assertRaisesRegex(ValueError, "Instruction words changed"):
                verify_reference(replace(self.reference, image=bytes(image)))


class TestWordStatePredicatePairCases(unittest.TestCase):
    def test_equal_adjacent_and_integer_boundaries(self):
        for address, spec in FUNCTIONS.items():
            for seed in (20261024, 7):
                cases = list(make_cases(address, seed, 12))
                self.assertEqual(len(cases), 19)
                self.assertEqual({case.label for case in cases[:7]},
                                 {f"boundary-{value:08x}" for value in
                                  (0, 1, spec["constant"] - 1, spec["constant"],
                                   spec["constant"] + 1, 0x7FFFFFFF, 0xFFFFFFFF)})


class TestWordStatePredicatePairExperiment(unittest.TestCase):
    def test_two_seeds_offset_constant_sense_and_caller_paths(self):
        for seed in (20261024, 7):
            with tempfile.TemporaryDirectory(prefix=f"smt4-word-state-{seed}-") as temporary:
                output = Path(temporary)
                subprocess.run(
                    [sys.executable,
                     str(ROOT / "tools/word_state_predicate_pair_experiment.py"),
                     "--seed", str(seed), "--samples", "64", "--output", str(output)],
                    cwd=ROOT, check=True, capture_output=True, text=True,
                )
                report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            self.assertEqual(len(report["functions"]), 2)
            self.assertTrue(all(row["passed"] and row["cases"] == 71
                                for row in report["functions"]))
            self.assertEqual(len(report["negative_controls"]), 6)
            self.assertTrue(all(row["detected"] for row in report["negative_controls"]))
            self.assertEqual(len(report["caller_windows"]), 4)
            self.assertTrue(all(row["passed"] for row in report["caller_windows"]))


if __name__ == "__main__":
    unittest.main()
