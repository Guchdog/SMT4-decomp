import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.scalar_0035d270_experiment import (
    ADDRESS, EXPECTED_FUNCTION_SHA256, ROOT, make_cases, run, verify_reference,
)
from tools.semantic_experiment import DATA


class TestScalar0035D270Pins(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            import csv
            cls.rows = list(csv.DictReader(stream))

    def test_exact_revision_and_function_bytes_are_pinned(self):
        result = verify_reference(self.image, self.game["code_sha256"], self.rows)
        record = result["functions"][hex(ADDRESS)]
        self.assertEqual(record["function_sha256"], EXPECTED_FUNCTION_SHA256)
        self.assertEqual(len(record["instructions"]), 5)

    def test_hash_and_instruction_drift_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, "0" * 64, self.rows)
        changed = bytearray(self.image)
        changed[ADDRESS - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(bytes(changed), hashlib.sha256(changed).hexdigest(), self.rows)


class TestScalar0035D270Cases(unittest.TestCase):
    def test_boundaries_and_seed_stream_are_well_formed(self):
        first = list(make_cases(17, samples=16))
        second = list(make_cases(18, samples=16))
        self.assertEqual(len(first), 24)
        self.assertNotEqual([case.data for case in first], [case.data for case in second])
        self.assertEqual(int.from_bytes(
            first[0].data[first[0].registers[0] - DATA + 0x18:
                          first[0].registers[0] - DATA + 0x1C], "little"), 0)
        self.assertEqual(int.from_bytes(
            first[1].data[first[1].registers[0] - DATA + 0x18:
                          first[1].registers[0] - DATA + 0x1C], "little"), 1)

    def test_candidate_and_wrong_zero_control(self):
        for seed in (17, 29):
            with tempfile.TemporaryDirectory(prefix="smt4-scalar-0035d270-") as temp_dir:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temp_dir),
                             seed=seed, samples=32)
            self.assertTrue(report["passed"])
            self.assertEqual(report["function"]["cases"], 40)
            self.assertEqual(report["function"]["original_bytes"], 20)
            self.assertTrue(report["negative_control"]["detected"])
            self.assertEqual(report["negative_control"]["reason"], "return value differs")
            self.assertIn("no direct caller window", " ".join(report["limitations"]))


if __name__ == "__main__":
    unittest.main()
