import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.three_word_copy_experiment import (
    ALL_ADDRESSES, EXPECTED_CALLERS, FUNCTIONS, ROOT, run, verify_reference,
)


class TestThreeWordCopyExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            import csv
            cls.ledger = list(csv.DictReader(stream))

    def test_reference_hash_instructions_and_direct_callers_are_pinned(self):
        reference = verify_reference(self.image, self.game["code_sha256"], self.ledger)
        self.assertEqual(set(int(address, 16) for address in reference["functions"]),
                         set(ALL_ADDRESSES))
        self.assertEqual(reference["direct_caller_counts"], {
            hex(address): len(EXPECTED_CALLERS[address]) for address in ALL_ADDRESSES
        })
        self.assertEqual({address: item["offset"] for address, item in FUNCTIONS.items()}, {
            0x00232B00: 0x4C, 0x00232B14: 0x40, 0x00232B28: 0x28,
        })

    def test_reference_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, "0" * 64, self.ledger)
        changed = bytearray(self.image)
        changed[ALL_ADDRESSES[0] - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Original instruction sequence changed"):
            verify_reference(bytes(changed), hashlib.sha256(changed).hexdigest(), self.ledger)

    def test_aliases_callers_and_negative_controls_on_two_seeds(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                              samples=1, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(len(report["functions"]), 3)
            self.assertTrue(all(item["passed"] for item in report["functions"]))
            self.assertEqual(report["function_comparisons"], 21)
            for function in report["functions"]:
                self.assertIn("exact-alias", function["directed_cases"])
                self.assertIn("destination-starts-after-source", function["directed_cases"])
                self.assertIn("destination-starts-before-source", function["directed_cases"])
                self.assertEqual(function["candidate_load_store_order"][0][0], "load")
            self.assertEqual(len(report["caller_results"]), 6)
            self.assertTrue(all(item["passed"] for item in report["caller_results"]))
            self.assertEqual(len(report["negative_controls"]), 2)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
