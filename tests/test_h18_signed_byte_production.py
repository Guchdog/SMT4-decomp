import tempfile
import unittest
from pathlib import Path

from tools.h18_signed_byte_production import run, verify_source

ROOT = Path(__file__).resolve().parents[1]


class TestH18SignedByteProduction(unittest.TestCase):
    def test_production_uses_alias_safe_byte_read_and_signed_result(self):
        contract = verify_source(ROOT)
        self.assertEqual(contract["symbol"], "func_00121d70")
        self.assertEqual(contract["byte_offset"], 0x330)
        self.assertEqual(contract["return_type"], "s32")
        self.assertTrue(contract["explicit_sign_extension"])
        self.assertEqual(contract["ledger_status"], "non_matching")

    def test_production_leaf_and_global_load_caller_composition(self):
        with tempfile.TemporaryDirectory() as temp:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temp), seed=7,
                         samples=8, caller_samples=256)
        self.assertTrue(report["passed"])
        self.assertTrue(report["function"]["passed"])
        self.assertEqual(report["function"]["directed_cases"], 256)
        self.assertTrue(report["caller_window"]["passed"])
        self.assertEqual(report["caller_window"]["start"], "0x110f3c")
        self.assertEqual(set(report["caller_window"]["continuations"]),
                         {"0x110f50", "0x111008"})
        self.assertTrue(all(row["detected"] for row in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
