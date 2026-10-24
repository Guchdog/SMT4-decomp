import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.conditional_record_writer_experiment import (
    FUNCTIONS, ROOT, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestConditionalRecordWriterExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )
        cls.image, cls.game_info, cls.ledger = (
            pinned.image, pinned.game_info, pinned.ledger
        )

    def test_exact_shapes_and_contract_are_pinned(self):
        reference = verify_reference(self.image, self.game_info, self.ledger)
        self.assertEqual(set(int(address, 16) for address in reference["functions"]),
                         set(FUNCTIONS))
        positive = reference["functions"]["0x35b254"]["observed_contract"]
        self.assertEqual(positive["condition"], "signed *(int32_t *)(r0+0x18) > 0")
        self.assertEqual(positive["counter"],
                         "u32 at r0+0x10 incremented modulo 2^32 after both record writes")
        self.assertEqual(positive["return"], "r0=0")

    def test_hash_and_instruction_drift_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, {**self.game_info, "code_sha256": "0" * 64},
                             self.ledger)
        changed = bytearray(self.image)
        changed[0x0035B254 - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Original instruction sequence changed"):
            verify_reference(bytes(changed),
                             {**self.game_info,
                              "code_sha256": hashlib.sha256(changed).hexdigest()},
                             self.ledger)

    def test_candidates_ordered_accesses_flags_and_fault_prefixes_on_two_seeds(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                             samples=8, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["function_comparisons"], 32)
            self.assertTrue(all(item["passed"] for item in report["functions"]))
            self.assertEqual(len(report["flag_checks"]), 10)
            self.assertTrue(all(item["original_flags_passed"]
                                for item in report["flag_checks"]))
            self.assertEqual(len(report["partial_fault_cases"]), 4)
            self.assertTrue(all(item["both_faulted"] and item["same_faulting_access"]
                                and item["same_partial_data"]
                                and item["same_write_footprint"]
                                and item["same_ordered_accesses"]
                                and item["first_store_survived"]
                                and item["counter_not_incremented"]
                                for item in report["partial_fault_cases"]))
            self.assertEqual(len(report["negative_controls"]), 1)
            self.assertTrue(report["negative_controls"][0]["detected"])
            for function in report["functions"]:
                traces = function["ordered_access_traces"]
                self.assertEqual(set(traces), {"zero-counter-zero", "positive-one-counter-one"})
                self.assertEqual([event[0] for event in traces["positive-one-counter-one"]],
                                 ["read", "read", "write", "read", "write", "read", "write"])


if __name__ == "__main__":
    unittest.main()
