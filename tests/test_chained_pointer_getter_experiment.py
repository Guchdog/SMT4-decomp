import hashlib
import csv
import json
import struct
import tempfile
import unittest
from pathlib import Path

from tools.chained_pointer_getter_experiment import (
    FUNCTIONS,
    PINNED_BYTES,
    ROOT,
    make_cases,
    run,
    verify_reference,
)
from tools.semantic_experiment import DATA


class TestChainedPointerGetterPins(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game_info = json.loads(
            (ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        with (ROOT / "config/functions.csv").open(
                encoding="utf-8", newline="") as stream:
            cls.ledger = list(csv.DictReader(stream))

    def test_all_three_functions_are_pinned_to_bytes_and_matching_ledger_rows(self):
        report = verify_reference(self.image, self.game_info, self.ledger)
        self.assertEqual(set(report["functions"]), {hex(address) for address in FUNCTIONS})
        for address, pinned in PINNED_BYTES.items():
            item = report["functions"][hex(address)]
            self.assertEqual(item["bytes_hex"], pinned)
            self.assertEqual(item["size"], 32)
            self.assertEqual(item["ledger"]["status"], "matching")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, self.game_info | {"code_sha256": "0" * 64},
                             self.ledger)

    def test_exact_bytes_reject_drift_after_image_hash_is_recomputed(self):
        changed = bytearray(self.image)
        changed[0x00207B78 - 0x00100000] ^= 1
        changed = bytes(changed)
        game = self.game_info | {"code_sha256": hashlib.sha256(changed).hexdigest()}
        with self.assertRaisesRegex(ValueError, "original bytes differ"):
            verify_reference(changed, game, self.ledger)


class TestChainedPointerGetterCases(unittest.TestCase):
    def test_null_intermediate_links_are_zero_and_remain_fault_cases(self):
        for address in FUNCTIONS:
            cases = {case.label: case for case in make_cases(address, seed=7, samples=3)}
            root = FUNCTIONS[address]["root"]
            first = DATA + 0x300
            root_slot = cases["null-first-link-fault"].registers[0] + root
            self.assertEqual(struct.unpack_from(
                "<I", cases["null-first-link-fault"].data, root_slot - DATA)[0], 0)
            self.assertEqual(struct.unpack_from(
                "<I", cases["null-second-link-fault"].data, first + 0x24 - DATA)[0], 0)
            self.assertEqual(len(cases), 12)

    def test_candidate_differential_faults_and_negative_controls(self):
        with tempfile.TemporaryDirectory(prefix="smt4-chained-pointer-getters-") as temp:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temp),
                         seed=7, samples=8)
        self.assertTrue(report["passed"])
        self.assertEqual(report["function_comparison_count"], 51)
        self.assertEqual(report["fault_case_count"], 6)
        self.assertEqual(report["negative_control_count"], 15)
        self.assertTrue(all(item["passed"] and item["case_count"] == 17
                            for item in report["candidate_functions"]))
        self.assertTrue(all(item["passed"] for item in report["fault_cases"]))
        self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
        self.assertFalse(report["caller_evidence"]["caller_windows_added"])
        self.assertTrue(all(not sites for sites in
                            report["caller_evidence"]["direct_bl_references"].values()))


if __name__ == "__main__":
    unittest.main()
