from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.semantic_experiment import Runner
from tools.signed_delta_experiment import (
    EXPECTED_SHA256, FUNCTIONS, ROOT, SIGNED_BOUNDARIES,
    make_cases, run, verify_reference,
)


class TestSignedDeltaReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            cls.ledger = list(csv.DictReader(stream))

    def test_pins_exact_image_ledger_words_order_and_offsets(self):
        evidence = verify_reference(self.image, self.ledger)
        self.assertEqual(evidence["code_sha256"], EXPECTED_SHA256)
        self.assertEqual(set(evidence["functions"]), {"0x1220c4", "0x1220d8"})
        for address, spec in FUNCTIONS.items():
            function = evidence["functions"][hex(address)]
            self.assertEqual(function["size"], 20)
            self.assertEqual(function["field_order"], [
                f"object+0x{spec['offset']:x} -> r0",
                f"object+0x{spec['offset'] + 4:x} -> r1",
            ])
            self.assertEqual(len(function["instruction_words"]), 5)

    def test_rehashed_mutation_and_ledger_drift_are_rejected(self):
        changed = bytearray(self.image)
        changed[0x001220C4 - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Unexpected code.bin SHA-256"):
            verify_reference(bytes(changed), self.ledger)
        ledger = [dict(row) for row in self.ledger]
        row = next(row for row in ledger if int(row["address"], 16) == 0x001220D8)
        row["size"] = "16"
        with self.assertRaisesRegex(ValueError, "Ledger entry changed"):
            verify_reference(self.image, ledger)


class TestSignedDeltaSemantics(unittest.TestCase):
    def test_boundaries_follow_signed_compare_and_modulo_subtraction(self):
        # Check the pinned original directly against the explicitly stated
        # two's-complement model, including CMP's retained NZCV flags.
        for address, spec in FUNCTIONS.items():
            runner = Runner(self.image_for_runner(), address)
            cases = list(make_cases(address, 0, 20261024))
            self.assertEqual(len(cases), len(SIGNED_BOUNDARIES) ** 2)
            for case in cases:
                offset = spec["offset"]
                base = case.registers[0]
                data_offset = base - 0x02000000 + offset
                left = int.from_bytes(case.data[data_offset:data_offset + 4], "little")
                right = int.from_bytes(case.data[data_offset + 4:data_offset + 8], "little")
                result = (right - left) & 0xFFFFFFFF
                left_signed = left if left < 0x80000000 else left - 0x100000000
                right_signed = right if right < 0x80000000 else right - 0x100000000
                expected_r0 = 0 if right_signed >= left_signed else (left - right) & 0xFFFFFFFF
                old = runner.run(case)
                self.assertIsNone(old.fault, case.label)
                self.assertEqual(old.result, expected_r0, case.label)
                n = (result >> 31) & 1
                z = int(result == 0)
                c = int(right >= left)
                v = int(bool(((right ^ left) & (right ^ result) & 0x80000000)))
                expected_nzcv = (n << 31) | (z << 30) | (c << 29) | (v << 28)
                self.assertEqual(old.nzcv, expected_nzcv, case.label)

    @staticmethod
    def image_for_runner():
        return (ROOT / "extracted/exefs/code.bin").read_bytes()

    def test_two_seed_differential_abi_flags_memory_faults_and_controls(self):
        for seed in (20261024, 7):
            output = ROOT / "build/semantic-equivalence" / f"signed-delta-seed{seed}"
            report = run(ROOT / "extracted/exefs/code.bin", output, seed, 128)
            self.assertTrue(report["passed"], json.dumps(report, indent=2))
            self.assertEqual(report["reference"]["code_sha256"], EXPECTED_SHA256)
            self.assertEqual(report["boundary_pairs_per_function"], 36)
            self.assertEqual(len(report["functions"]), 2)
            for item in report["functions"]:
                self.assertTrue(item["passed"], item)
                self.assertTrue(item["candidate_bytes_equal"], item)
                self.assertEqual(item["original_bytes"], 20)
                self.assertEqual(item["candidate_bytes"], 20)
                self.assertEqual(item["cases"], 164)
            self.assertEqual(len(report["negative_controls"]), 3)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
            self.assertEqual(len(report["fault_behavior"]), 2)
            self.assertTrue(all(item["passed"] for item in report["fault_behavior"]))
            self.assertEqual(report["caller_windows"], [])
            self.assertTrue((output / "report.json").is_file())


if __name__ == "__main__":
    unittest.main()
