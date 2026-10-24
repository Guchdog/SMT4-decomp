import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.title_cursor_experiment import (
    ROOT, PROVISIONAL_VALUES, run, verify_reference_block,
)


class TestTitleCursorExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))

    def test_pinned_reference_contains_the_exact_six_instruction_block(self):
        reference = verify_reference_block(self.image, self.game["code_sha256"])
        self.assertEqual(len(reference["instructions"]), 6)
        self.assertEqual(reference["instructions"][0]["address"], "0x1e9dac")
        self.assertEqual(reference["instructions"][-1]["address"], "0x1e9dc0")

    def test_reference_hash_and_block_bytes_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference_block(self.image, "0" * 64)
        changed = bytearray(self.image)
        changed[0x001E9DAC - 0x00100000] ^= 1
        changed = bytes(changed)
        with self.assertRaisesRegex(ValueError, "six recorded instructions"):
            verify_reference_block(changed, hashlib.sha256(changed).hexdigest())

    def test_positive_model_and_targeted_negative_control(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temp_dir), seed=7)
        self.assertTrue(report["passed"])
        self.assertEqual(report["provisional_values"], list(PROVISIONAL_VALUES))
        self.assertEqual(len(report["cases"]), 6)
        self.assertTrue(all(case["passed"] for case in report["cases"]))
        self.assertTrue(report["negative_control"]["detected"])
        self.assertEqual(report["negative_control"]["case"], "provisional--1")


if __name__ == "__main__":
    unittest.main()
