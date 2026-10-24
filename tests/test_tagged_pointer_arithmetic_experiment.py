import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tools.semantic_experiment_support import load_pinned_reference
from tools.tagged_pointer_arithmetic_experiment import (
    CALLER_WINDOWS, FUNCTIONS, ROOT, make_cases, verify_reference,
)


class TestTaggedPointerArithmeticReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv")

    def test_code_instructions_direct_callers_and_consumers_are_pinned(self):
        report = verify_reference(self.reference)
        self.assertEqual(set(report["functions"]), {hex(a) for a in FUNCTIONS})
        self.assertEqual(sum(row["direct_call_count"]
                             for row in report["functions"].values()), 4)
        self.assertEqual(set(report["callers"]), {hex(a) for a in CALLER_WINDOWS})

    def test_mutated_instruction_words_are_rejected(self):
        for address in FUNCTIONS:
            image = bytearray(self.reference.image)
            image[address - 0x00100000] ^= 1
            with self.assertRaisesRegex(ValueError, "Instruction words changed"):
                verify_reference(replace(self.reference, image=bytes(image)))


class TestTaggedPointerArithmeticCases(unittest.TestCase):
    def test_gate_and_modular_boundaries_are_crossed(self):
        tags = {"0000", "0001", "0100", "0101", "0102", "ffff"}
        displacements = {0, 1, 0x20, 0x100, 0x7FFFFFFF, 0xFFFFFF00,
                         0xFFFFFFF0, 0xFFFFFFFF}
        for address in FUNCTIONS:
            for seed in (20261024, 7):
                cases = list(make_cases(address, seed, 8))
                self.assertEqual(len(cases), 56)
                self.assertTrue(all(any(f"tag-{tag}-" in case.label for case in cases)
                                    for tag in tags))
                self.assertTrue(all(any(f"disp-{value:08x}" in case.label for case in cases)
                                    for value in displacements))


class TestTaggedPointerArithmeticExperiment(unittest.TestCase):
    def test_two_seed_runs_wraparound_footprint_negatives_and_callers(self):
        for seed in (20261024, 7):
            with tempfile.TemporaryDirectory(prefix=f"smt4-tagged-pointer-{seed}-") as temporary:
                output = Path(temporary)
                subprocess.run(
                    [sys.executable,
                     str(ROOT / "tools/tagged_pointer_arithmetic_experiment.py"),
                     "--seed", str(seed), "--samples", "64", "--output", str(output)],
                    cwd=ROOT, check=True, capture_output=True, text=True,
                )
                report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            self.assertEqual(len(report["functions"]), 2)
            self.assertTrue(all(row["passed"] and row["cases"] == 112
                                for row in report["functions"]))
            self.assertEqual(len(report["negative_controls"]), 6)
            self.assertTrue(all(row["detected"] for row in report["negative_controls"]))
            self.assertEqual(len(report["caller_windows"]), 2)
            self.assertTrue(all(row["passed"] for row in report["caller_windows"]))


if __name__ == "__main__":
    unittest.main()
