import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.triple_conditional_store_experiment import (
    ADDRESS, CALLER, EXPECTED_BYTES, ROOT,
    run, verify_reference,
)


class TestTripleConditionalStoreExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            import csv
            cls.ledger = list(csv.DictReader(stream))

    def test_exact_body_ledger_and_manually_pinned_caller(self):
        evidence = verify_reference(self.image, self.game, self.ledger)
        self.assertEqual(ADDRESS, 0x0034F978)
        self.assertEqual(CALLER, 0x0034F284)
        self.assertEqual(evidence["ledger_status"], "matching")
        self.assertEqual(evidence["size"], 24)
        self.assertEqual(bytes.fromhex(evidence["function_bytes_hex"]), EXPECTED_BYTES)
        self.assertEqual(evidence["direct_callers"], ["0x34f284"])
        self.assertEqual(evidence["caller_window"], [
            "push {r3, r4, r5, lr}", "mov r4, r0", "bl #0x34f978",
            "cmp r0, #0", "beq #0x34f304",
        ])

    def test_reference_rejects_changed_pin(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, {**self.game, "code_sha256": "0" * 64}, self.ledger)
        changed = bytearray(self.image)
        changed[ADDRESS - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(bytes(changed), self.game, self.ledger)

    def test_two_seeds_guards_alias_order_abi_nzcv_callers_fault_and_controls(self):
        reports = []
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                             samples=1, seed=seed)
            reports.append(report)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["functional_cases"], 9)
            self.assertTrue(all(case["passed"] for case in report["functional_comparisons"]))
            self.assertTrue(all(case["nzcv_equal"] for case in report["functional_comparisons"]))
            self.assertEqual(report["nzcv"]["equal_cases"], 9)
            self.assertEqual(report["candidate_bytes"], 32)
            stores = [instruction for instruction in report["candidate_instructions"]
                      if instruction.startswith("strne ")]
            self.assertEqual(len(stores), 3)
            self.assertTrue(all(item["passed"] for item in report["caller_windows"]))
            self.assertEqual(len(report["caller_windows"]), 2)
            self.assertEqual(len(report["negative_controls"]), 5)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
            fault = report["fault_probe"]
            self.assertFalse(fault["equivalence_claimed"])
            self.assertTrue(fault["footprint_equal"])
            self.assertTrue(fault["original"]["faulted"])
            self.assertTrue(fault["candidate"]["faulted"])
            self.assertEqual(len(fault["original"]["write_bytes"]), 8)
            self.assertEqual(fault["original"]["write_bytes"],
                             fault["candidate"]["write_bytes"])
            self.assertIn("STM multi-register atomicity", " ".join(report["limitations"]))

        self.assertEqual([report["seed"] for report in reports], [7, 20261024])


if __name__ == "__main__":
    unittest.main()
