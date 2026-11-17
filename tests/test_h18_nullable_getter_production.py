import tempfile
import unittest
from pathlib import Path

from tools.h18_nullable_getter_production import run, verify_source

ROOT = Path(__file__).resolve().parents[1]


class TestH18NullableGetterProduction(unittest.TestCase):
    def test_production_preserves_nullable_void_pointer_abi_without_record_type(self):
        contract = verify_source(ROOT)
        self.assertEqual(contract["symbol"], "engine_func_0014ec5c")
        self.assertEqual(contract["field_offset"], 0x1C)
        self.assertEqual(contract["input_type"], "void*")
        self.assertEqual(contract["return_type"], "void*")
        self.assertTrue(contract["null_guard"])
        self.assertEqual(contract["ledger_status"], "non_matching")

    def test_production_leaf_and_both_guarded_callers(self):
        with tempfile.TemporaryDirectory() as temp:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temp), seed=7,
                         samples=8, caller_randomized=4)
        self.assertTrue(report["passed"])
        self.assertTrue(report["function"]["passed"])
        self.assertIn("null_input", {case["kind"] for case in report["function"]["results"]})
        self.assertIn("nonnull_zero_field", {case["kind"] for case in report["function"]["results"]})
        self.assertIn("nonnull_pointer_field", {case["kind"] for case in report["function"]["results"]})
        self.assertEqual(len(report["callers"]), 2)
        self.assertTrue(all(caller["passed"] for caller in report["callers"]))
        self.assertTrue(all(control["detected"] for control in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
