import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.engine_leaf_experiment import (
    COPY_OFFSET, COPY_PLAIN, GETTERS, ROOT, run, verify_reference,
)


class TestEngineLeafExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            import csv
            cls.rows = list(csv.DictReader(stream))

    def test_pinned_reference_has_all_requested_function_shapes(self):
        specs = verify_reference(self.image, self.game["code_sha256"], self.rows)
        self.assertEqual(len(specs), 19)
        self.assertEqual(sum(item.kind == "plain_copy" for item in specs), 8)
        self.assertEqual(sum(item.kind == "offset_copy" for item in specs), 7)
        self.assertEqual(sum(item.kind == "getter" for item in specs), 4)
        self.assertEqual({item.address for item in specs},
                         set(COPY_PLAIN) | set(COPY_OFFSET) | set(GETTERS))

    def test_reference_hash_and_instruction_shapes_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, "0" * 64, self.rows)
        changed = bytearray(self.image)
        changed[0x002C7084 - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Original instructions changed"):
            verify_reference(bytes(changed), hashlib.sha256(changed).hexdigest(), self.rows)

    def test_all_candidates_and_negative_controls(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                          samples=1, seed=7)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["functions"]), 19)
        self.assertEqual(sum(row["passed"] for row in report["functions"]), 19)
        self.assertEqual(sum(row["cases"] for row in report["functions"]),
                         15 * 6 + 4 * 9)
        self.assertEqual(len(report["negative_controls"]), 3)
        self.assertTrue(all(row["detected"] for row in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
