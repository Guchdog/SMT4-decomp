from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.signed_byte_pair_experiment import (
    EXPECTED_SHA256, FUNCTIONS, ROOT, make_cases, run, verify_reference,
)


class TestSignedBytePairReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        import csv
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            cls.ledger = list(csv.DictReader(stream))

    def test_only_two_new_signed_byte_getters_are_pinned(self):
        report = verify_reference(self.image, self.ledger)
        self.assertEqual(report["code_sha256"], EXPECTED_SHA256)
        self.assertEqual(set(report["functions"]), {hex(address) for address in FUNCTIONS})
        self.assertNotIn("0x121d70", report["functions"])
        self.assertEqual({item["effective_offset"] for item in report["functions"].values()},
                         {"0x556", "0x45e"})

    def test_rehashed_instruction_mutation_is_rejected(self):
        changed = bytearray(self.image)
        changed[0x003E6368 - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Unexpected code.bin SHA-256"):
            verify_reference(bytes(changed), self.ledger)


class TestSignedBytePairInputs(unittest.TestCase):
    def test_signed_boundaries_and_two_seeded_input_sets(self):
        for address, spec in FUNCTIONS.items():
            for seed in (20261024, 7):
                generated = list(make_cases(address, 128, seed))
                self.assertEqual(len(generated), 134)
                self.assertEqual([case.data[case.registers[0] - 0x02000000 + spec["offset"]]
                                  for case in generated[:6]], [0, 1, 0x7F, 0x80, 0xFE, 0xFF])
                for case in generated:
                    self.assertEqual(len(case.data), 0x1000)


class TestSignedBytePairDifferential(unittest.TestCase):
    def test_two_seed_runs_cover_access_fault_and_all_negative_controls(self):
        totals = {address: 0 for address in FUNCTIONS}
        negative_count = 0
        fault_count = 0
        for seed in (20261024, 7):
            with tempfile.TemporaryDirectory(prefix=f"smt4-signed-byte-{seed}-") as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary), seed, 128)
                self.assertTrue(report["passed"], json.dumps(report, indent=2))
            self.assertEqual(len(report["functions"]), 2)
            for item in report["functions"]:
                self.assertTrue(item["passed"])
                self.assertEqual(item["cases"], 134)
                totals[int(item["address"], 16)] += item["cases"]
            self.assertEqual(len(report["negative_controls"]), 6)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
            negative_count += len(report["negative_controls"])
            self.assertEqual(len(report["fault_behavior"]), 2)
            self.assertTrue(all(item["passed"] for item in report["fault_behavior"]))
            fault_count += len(report["fault_behavior"])
            self.assertEqual(report["caller_windows"], [])
        self.assertEqual(totals, {0x003E6368: 268, 0x003E8878: 268})
        self.assertEqual(negative_count, 12)
        self.assertEqual(fault_count, 4)


if __name__ == "__main__":
    unittest.main()
