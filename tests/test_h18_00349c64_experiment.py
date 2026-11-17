import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.h18_00349c64_experiment import ROOT, make_cases, verify_reference


class TestConstantReturnContract(unittest.TestCase):
    def test_reference_is_the_eight_byte_arm_entry_inside_compound_span(self):
        evidence = verify_reference(ROOT / "extracted/exefs/code.bin")
        self.assertEqual(evidence["entry_bytes"], "0100a0e31eff2fe1")
        self.assertEqual(evidence["entry_size"], 8)
        self.assertEqual(evidence["catalog_span_size"], 720)
        self.assertEqual(evidence["adjacent_entry"], "0x00349c70")
        self.assertEqual(evidence["direct_callers"], [])
        self.assertEqual(evidence["aligned_function_pointer_sites"],
                         [f"0x{address:08x}" for address in range(0x0047299C,
                                                                    0x004729B4, 4)])

    def test_cases_vary_general_registers_flags_and_memory(self):
        cases = list(make_cases(seed=7, samples=8))
        self.assertEqual(len(cases), 8)
        self.assertGreater(len({case.nzcv for case in cases}), 1)
        self.assertGreater(len({case.registers for case in cases}), 1)
        self.assertGreater(len({case.data for case in cases}), 1)
        self.assertGreater(len({case.stack for case in cases}), 1)


class TestConstantReturnExperiment(unittest.TestCase):
    def test_two_seed_differential_and_three_negative_controls(self):
        for seed in (20261024, 7):
            with tempfile.TemporaryDirectory(prefix=f"smt4-h18-349c64-{seed}-") as directory:
                output = Path(directory)
                subprocess.run(
                    [sys.executable, str(ROOT / "tools/h18_00349c64_experiment.py"),
                     "--code", str(ROOT / "extracted/exefs/code.bin"),
                     "--seed", str(seed), "--samples", "16", "--output", str(output)],
                    cwd=ROOT, check=True, capture_output=True, text=True)
                report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"], report)
            self.assertEqual(report["seed"], seed)
            self.assertEqual(report["cases"], 16)
            self.assertTrue(report["negative_controls"])
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
            self.assertEqual({item["name"] for item in report["negative_controls"]},
                             {"wrong_return", "changed_flags", "wrote_memory"})


if __name__ == "__main__":
    unittest.main()
