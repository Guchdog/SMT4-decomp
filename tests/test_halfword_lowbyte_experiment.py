import tempfile
import subprocess
import sys
import unittest
from pathlib import Path

from tools.halfword_lowbyte_experiment import (
    CALLER_WINDOWS, EXPECTED_SHA256, FUNCTIONS, ROOT,
    make_cases, run, verify_caller_windows, verify_reference,
)


class TestHalfwordLowbyteReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            import csv
            cls.ledger = list(csv.DictReader(stream))

    def test_hash_instruction_words_and_sixteen_direct_callers_are_pinned(self):
        report = verify_reference(self.image, self.ledger)
        self.assertEqual(report["code_sha256"], EXPECTED_SHA256)
        self.assertEqual(set(report["functions"]), {hex(address) for address in FUNCTIONS})
        self.assertEqual(sum(item["direct_call_count"]
                             for item in report["functions"].values()), 32)

    def test_rehashed_instruction_mutation_is_rejected(self):
        changed = bytearray(self.image)
        changed[0x002345F0 - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Unexpected code.bin SHA-256"):
            verify_reference(bytes(changed), self.ledger)

    def test_original_caller_windows_are_pinned(self):
        windows = verify_caller_windows(self.image)
        self.assertEqual(set(windows), {hex(address) for address in CALLER_WINDOWS})


class TestHalfwordLowbyteInputs(unittest.TestCase):
    def test_boundaries_and_seeded_samples_preserve_distinct_high_byte_markers(self):
        for address, spec in FUNCTIONS.items():
            for seed in (20261024, 7):
                generated = list(make_cases(address, 16, seed))
                self.assertEqual(len(generated), 22)
                self.assertEqual({case.label.split("-")[1] for case in generated[:6]},
                                 {"00", "01", "7f", "80", "fe", "ff"})
                for case in generated:
                    base = case.registers[0] - 0x02000000
                    self.assertNotEqual(case.data[base + spec["offset"] + 1], 0)
                    self.assertEqual(len(case.data), 0x1000)


class TestHalfwordLowbyteExperiment(unittest.TestCase):
    def test_two_seed_differential_runs_and_negative_controls(self):
        for seed in (20261024, 7):
            with tempfile.TemporaryDirectory(prefix=f"smt4-halfword-{seed}-") as temporary:
                output = Path(temporary)
                subprocess.run(
                    [sys.executable, str(ROOT / "tools/halfword_lowbyte_experiment.py"),
                     "--seed", str(seed), "--samples", "64", "--output", str(output)],
                    cwd=ROOT, check=True, capture_output=True, text=True,
                )
                report = __import__("json").loads(
                    (output / "report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            self.assertEqual(len(report["functions"]), 2)
            self.assertTrue(all(item["passed"] and item["cases"] == 70
                                for item in report["functions"]))
            self.assertEqual(len(report["negative_controls"]), 4)
            self.assertTrue(all(item["detected"]
                                for item in report["negative_controls"]))
            self.assertEqual(len(report["caller_window_results"]), 2)
            self.assertTrue(all(item["passed"]
                                for item in report["caller_window_results"]))
            self.assertEqual(report["reference"]["code_sha256"], EXPECTED_SHA256)


if __name__ == "__main__":
    unittest.main()
