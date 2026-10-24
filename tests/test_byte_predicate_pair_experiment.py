import json
from dataclasses import replace
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.byte_predicate_pair_experiment import (
    CALLER_WINDOWS, FUNCTIONS, ROOT, make_cases, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestBytePredicatePairReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv")

    def test_image_instructions_callers_and_consumer_windows_are_pinned(self):
        evidence = verify_reference(self.reference)
        self.assertEqual(set(evidence["functions"]), {hex(a) for a in FUNCTIONS})
        self.assertEqual(sum(item["direct_call_count"]
                             for item in evidence["functions"].values()), 17)
        self.assertEqual(set(evidence["caller_windows"]),
                         {hex(a) for a in CALLER_WINDOWS})

    def test_instruction_mutations_fail_closed(self):
        for address in FUNCTIONS:
            image = bytearray(self.reference.image)
            image[address - 0x00100000] ^= 1
            with self.assertRaisesRegex(ValueError, "Instruction words changed"):
                verify_reference(replace(self.reference, image=bytes(image)))


class TestBytePredicatePairCases(unittest.TestCase):
    def test_full_byte_domain_and_seeded_register_state(self):
        for address in FUNCTIONS:
            for seed in (20261024, 7):
                cases = list(make_cases(address, seed, 16))
                self.assertEqual(len(cases), 272)
                self.assertEqual({case.label for case in cases[:256]},
                                 {f"byte-{value:02x}" for value in range(256)})
                self.assertTrue(all(len(case.data) == 0x1000 for case in cases))


class TestBytePredicatePairExperiment(unittest.TestCase):
    def test_two_seed_runs_with_offset_constant_sense_and_caller_controls(self):
        for seed in (20261024, 7):
            with tempfile.TemporaryDirectory(prefix=f"smt4-byte-predicate-{seed}-") as temporary:
                output = Path(temporary)
                subprocess.run(
                    [sys.executable, str(ROOT / "tools/byte_predicate_pair_experiment.py"),
                     "--seed", str(seed), "--samples", "64", "--output", str(output)],
                    cwd=ROOT, check=True, capture_output=True, text=True,
                )
                report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            self.assertEqual(len(report["functions"]), 2)
            self.assertTrue(all(item["passed"] and item["cases"] == 320
                                for item in report["functions"]))
            self.assertEqual(len(report["negative_controls"]), 6)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
            self.assertEqual(len(report["caller_windows"]), 4)
            self.assertTrue(all(item["passed"] for item in report["caller_windows"]))


if __name__ == "__main__":
    unittest.main()
