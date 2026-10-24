import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tools.semantic_experiment_support import load_pinned_reference
from tools.vfp_lane_add_experiment import (
    FLOAT_EDGES, FUNCTIONS, ROOT, make_cases, verify_reference,
)


class TestVfpLaneAddReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv")

    def test_instruction_words_and_ledger_are_pinned(self):
        report = verify_reference(self.reference)
        self.assertEqual(set(report["functions"]), {hex(a) for a in FUNCTIONS})
        self.assertEqual(report["caller_evidence"],
                         "None collected; no caller behavior is claimed.")

    def test_mutated_reference_instruction_is_rejected(self):
        address = next(iter(FUNCTIONS))
        image = bytearray(self.reference.image)
        image[address - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Instruction words changed"):
            verify_reference(replace(self.reference, image=bytes(image)))


class TestVfpLaneAddCases(unittest.TestCase):
    def test_ieee_edges_and_alias_layouts_are_included_for_both_seeds(self):
        for address in FUNCTIONS:
            for seed in (20261024, 7):
                cases = list(make_cases(address, seed, 8))
                self.assertEqual(len(cases), len(FLOAT_EDGES) + 32 + 6 + 8)
                labels = {case.label for case in cases}
                self.assertTrue(all(f"edge-{index:02d}-" in " ".join(labels)
                                    for index in range(len(FLOAT_EDGES))))
                self.assertEqual(sum(label.startswith("alias-") for label in labels), 6)
                for case in cases:
                    self.assertTrue(0x02000100 <= case.registers[0] < 0x02000400)
                    self.assertEqual(len(case.vfp), 32)


class TestVfpLaneAddExperiment(unittest.TestCase):
    def test_two_seeds_fp_mode_aliases_and_negative_controls(self):
        for seed in (20261024, 7):
            with tempfile.TemporaryDirectory(prefix=f"smt4-vfp-lane-add-{seed}-") as temporary:
                output = Path(temporary)
                subprocess.run(
                    [sys.executable,
                     str(ROOT / "tools/vfp_lane_add_experiment.py"),
                     "--seed", str(seed), "--samples", "32", "--output", str(output)],
                    cwd=ROOT, check=True, capture_output=True, text=True,
                )
                report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            self.assertEqual(report["pinned_fpscr"], "0x00000000")
            self.assertEqual(len(report["functions"]), 2)
            self.assertTrue(all(row["passed"] and row["cases"] == len(FLOAT_EDGES) + 32 + 6 + 32
                                for row in report["functions"]))
            self.assertTrue(all(row["caller_saved_state_diff_cases"] > 0
                                for row in report["functions"]))
            self.assertEqual(len(report["negative_controls"]), 4)
            self.assertTrue(all(row["detected"] for row in report["negative_controls"]))
            self.assertIn("Caller-saved s0-s15", " ".join(report["limitations"]))
            self.assertIn("No callers were manually inspected", " ".join(report["limitations"]))


if __name__ == "__main__":
    unittest.main()
