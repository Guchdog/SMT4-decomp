import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.semantic_experiment_support import load_pinned_reference
from tools.packed_word_helper_experiment import FUNCTIONS, ROOT, make_cases, verify_reference


class TestPackedWordHelperPins(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv")

    def test_instruction_words_pointer_slots_and_bounded_caller_search(self):
        evidence = verify_reference(self.reference)
        self.assertEqual(set(evidence["functions"]), {hex(x) for x in FUNCTIONS})
        self.assertEqual(evidence["caller_evidence"]["observation"],
                         "No direct ARM BL instruction in the aligned-word scan targets any of the three leaves.")
        self.assertEqual(len(evidence["observed_data_pointer_slots"]), 3)
        self.assertTrue(all(not row["direct_arm_bl_sites"]
                            for row in evidence["functions"].values()))

    def test_mutated_function_word_rejected(self):
        from dataclasses import replace
        address = next(iter(FUNCTIONS))
        image = bytearray(self.reference.image)
        image[address - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Instruction words changed"):
            verify_reference(replace(self.reference, image=bytes(image)))


class TestPackedWordHelperInputs(unittest.TestCase):
    def test_directed_and_seeded_cases_cover_full_u32_inputs(self):
        address = next(iter(FUNCTIONS))
        cases = list(make_cases(address, 7, 8))
        self.assertEqual(len(cases), 6 ** 4 + 32 + 7 + 8)
        self.assertEqual(cases[0].registers[1:4], (0, 0, 0))
        self.assertTrue(any(case.registers[1] == 0xFFFFFFFF for case in cases))
        self.assertTrue(any(int.from_bytes(case.stack[0x1000:0x1004], "little") == 0xFFFFFFFF
                            for case in cases))


class TestPackedWordHelperExperiment(unittest.TestCase):
    def test_two_seeds_register_result_memory_fault_and_negative_controls(self):
        for seed in (20261024, 7):
            with tempfile.TemporaryDirectory(prefix=f"smt4-packed-word-{seed}-") as temporary:
                output = Path(temporary)
                subprocess.run(
                    [sys.executable, str(ROOT / "tools/packed_word_helper_experiment.py"),
                     "--seed", str(seed), "--samples", "8", "--output", str(output)],
                    cwd=ROOT, check=True, capture_output=True, text=True,
                )
                report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            self.assertEqual(len(report["functions"]), 3)
            self.assertTrue(all(row["passed"] and row["cases"] == 6 ** 4 + 32 + 7 + 8
                                for row in report["functions"]))
            self.assertEqual(len(report["negative_controls"]), 12)
            self.assertTrue(all(row["detected"] for row in report["negative_controls"]))
            self.assertTrue(all(row["passed"] for row in report["fault_footprint"]))


if __name__ == "__main__":
    unittest.main()
