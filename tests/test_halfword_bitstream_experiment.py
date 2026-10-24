from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.halfword_bitstream_experiment import (
    EXPECTED_SHA256, FUNCTIONS, ROOT, _ledger, _expected_model,
    verify_reference,
)


class TestHalfwordBitstreamReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.ledger = _ledger()

    def test_identical_leaf_bytes_and_all_direct_blt_callers_are_pinned(self):
        report = verify_reference(self.image, self.ledger)
        self.assertEqual(report["code_sha256"], EXPECTED_SHA256)
        self.assertEqual(set(report["functions"]), {f"0x{x:08x}" for x in FUNCTIONS})
        for address, item in report["functions"].items():
            self.assertEqual(item["size"], 20)
            self.assertEqual(item["direct_call_count"], 33)
            self.assertEqual(len(item["caller_windows"]), 33)
            self.assertEqual(item["caller_subtract_operand_classes"], {
                "r6": 16, "immediate": 11, "r7": 3, "r5": 3,
            })
            self.assertTrue(all(caller["condition"] == "LT"
                                and caller["flags_preserved_between_sub_and_call"]
                                for caller in item["caller_windows"]))

    def test_rehashed_instruction_mutation_is_rejected(self):
        changed = bytearray(self.image)
        changed[0x0016E468 - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Unexpected code.bin SHA-256"):
            verify_reference(bytes(changed), self.ledger)


class TestHalfwordBitstreamModel(unittest.TestCase):
    def test_all_shift_residues_match_arm_register_lsl_rules(self):
        for amount in range(256):
            count = (-amount) & 0xFFFFFFFF
            expected_shifted = (0xA55A if amount == 0 else
                                ((0xA55A << amount) & 0xFFFFFFFF if amount < 32 else 0))
            self.assertEqual(_expected_model(0xA55A, count, 0), expected_shifted)
        self.assertEqual(_expected_model(0xA55A, 0, 0), 0xA55A)
        self.assertEqual(_expected_model(0xA55A, 0xFFFFFFFF, 0), 0x14AB4)
        self.assertEqual(_expected_model(0xA55A, 0xFFFFFFDE, 0), 0)

    def test_two_seed_differential_runs_confirm_value_model_but_gate_replacement(self):
        for seed in (20261024, 7):
            with tempfile.TemporaryDirectory(prefix=f"smt4-halfword-bitstream-{seed}-") as temporary:
                output = Path(temporary)
                subprocess.run(
                    [sys.executable, str(ROOT / "tools/halfword_bitstream_experiment.py"),
                     "--seed", str(seed), "--output", str(output)],
                    cwd=ROOT, check=True, capture_output=True, text=True,
                )
                report = json.loads((output / "report.json").read_text(encoding="utf-8"))

            self.assertTrue(report["passed"])
            self.assertFalse(report["abi_gate"]["direct_normal_cpp_replacement_compatible"])
            self.assertEqual(report["reference"]["code_sha256"], EXPECTED_SHA256)
            self.assertIsNone(report["input_contract"]["caller_proven_numeric_r2_range"][
                "established_range"])
            self.assertEqual(len(report["functions"]), 3)
            for function in report["functions"]:
                self.assertEqual(function["tested_cases"], 1024)
                self.assertEqual(function["effective_shift_residues"], 256)
                self.assertEqual(function["counts"]["value_matches"], 1024)
                self.assertEqual(function["counts"]["expected_reads"], 1024)
                self.assertEqual(function["counts"]["no_writes"], 1024)
                self.assertEqual(function["counts"]["original_flags_unchanged"], 1024)
                self.assertEqual(function["counts"]["candidate_aapcs_preserved"], 1024)
                self.assertEqual(function["replacement_state_mismatch_cases"]["r1"], 1024)
                self.assertEqual(function["replacement_state_mismatch_cases"]["r9"], 1024)
                self.assertEqual(function["replacement_state_mismatch_cases"]["r10"], 1024)
            self.assertEqual(len(report["negative_controls"]), 6)
            self.assertTrue(all(control["detected"]
                                for control in report["negative_controls"]))
            self.assertEqual(len(report["caller_window_probes"]), 3)
            for probe in report["caller_window_probes"]:
                self.assertTrue(probe["original_stopped_after_call"])
                self.assertTrue(probe["candidate_stopped_after_call"])
                self.assertFalse(probe["direct_replacement_state_matches"])
                self.assertEqual(probe["caller_proven_input_r2"],
                                 "0x00000000 before subs r2,#1; -1 at helper entry")
                self.assertEqual(probe["original_r2"], "0x0000000f")
                self.assertEqual(probe["candidate_return_r0"], probe["original_r3"])


if __name__ == "__main__":
    unittest.main()
