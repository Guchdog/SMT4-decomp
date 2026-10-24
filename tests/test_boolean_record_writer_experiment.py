import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.boolean_record_writer_experiment import (
    FUNCTIONS, ROOT, run, verify_reference,
)


class TestBooleanRecordWriterExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            import csv
            cls.ledger = list(csv.DictReader(stream))

    def test_exact_instruction_pins_and_revision_hash(self):
        evidence = verify_reference(self.image, self.game, self.ledger)
        self.assertEqual(set(map(int, (int(key, 16) for key in evidence["functions"]))),
                         set(FUNCTIONS))
        self.assertEqual({int(key, 16): value["size"]
                          for key, value in evidence["functions"].items()},
                         {address: 88 for address in FUNCTIONS})
        changed = bytearray(self.image)
        changed[next(iter(FUNCTIONS)) - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(bytes(changed), self.game, self.ledger)
        with self.assertRaisesRegex(ValueError, "instruction sequence changed"):
            verify_reference(bytes(changed),
                             {**self.game, "code_sha256": hashlib.sha256(changed).hexdigest()},
                             self.ledger)

    def test_two_seed_differential_runs_faults_and_negative_controls(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                             samples=48, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["function_comparisons"], 106)
            self.assertTrue(all(item["passed"] for item in report["functions"]))
            self.assertEqual(len(report["negative_controls"]), 2)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
            self.assertEqual(len(report["partial_fault_cases"]), 6)
            self.assertTrue(all(item["both_faulted"] and item["same_faulting_access"]
                                and item["same_ordered_accesses"]
                                and item["same_partial_data"]
                                and item["same_write_footprint"]
                                and item["cursor_first_increment_committed"]
                                and item["byte_store_committed_before_word_fault"] is not False
                                for item in report["partial_fault_cases"]))
            self.assertEqual(report["callers"]["verified"], [])


if __name__ == "__main__":
    unittest.main()
