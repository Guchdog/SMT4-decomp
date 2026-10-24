import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.table_callback_experiment import (
    ALL_ADDRESSES, BYTE_CALLBACKS, HALFWORD_CALLBACKS, ROOT, run,
    verify_reference,
)


class TestTableCallbackExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            import csv
            cls.rows = list(csv.DictReader(stream))

    def test_pinned_table_and_17_instruction_shapes(self):
        specs = verify_reference(self.image, self.game["code_sha256"], self.rows)
        self.assertEqual({spec.address for spec in specs}, set(ALL_ADDRESSES))
        self.assertEqual(sum(spec.width == "byte" for spec in specs), 11)
        self.assertEqual(sum(spec.width == "halfword" for spec in specs), 6)
        self.assertEqual(set(BYTE_CALLBACKS) | set(HALFWORD_CALLBACKS), set(ALL_ADDRESSES))

    def test_reference_and_instruction_changes_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, "0" * 64, self.rows)
        changed = bytearray(self.image)
        changed[ALL_ADDRESSES[0] - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Original instructions changed"):
            verify_reference(bytes(changed), hashlib.sha256(changed).hexdigest(), self.rows)

    def test_all_candidates_and_negative_controls(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                          samples=1, seed=7)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["functions"]), 17)
        self.assertTrue(all(row["passed"] for row in report["functions"]))
        self.assertEqual(sum(row["cases"] for row in report["functions"]), 17 * 9)
        self.assertEqual(len(report["negative_controls"]), 2)
        self.assertTrue(all(row["detected"] for row in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
