import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.scalar_predicate_experiment import (
    CALLER_WINDOWS, FUNCTIONS, ROOT, make_cases, run, verify_callers,
    verify_reference,
)
from tools.semantic_experiment import DATA, DATA_SIZE


class TestScalarPredicateReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            import csv
            cls.rows = list(csv.DictReader(stream))

    def test_hash_and_all_four_instruction_shapes_are_pinned(self):
        result = verify_reference(self.image, self.game["code_sha256"], self.rows)
        self.assertEqual(set(result["functions"]), {hex(address) for address in FUNCTIONS})
        self.assertEqual(len(result["functions"]), 4)

    def test_reference_and_caller_pins_fail_closed_on_drift(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, "0" * 64, self.rows)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_callers(self.image, "0" * 64)
        changed = bytearray(self.image)
        changed[0x003358E0 - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Original instructions changed"):
            verify_reference(bytes(changed), hashlib.sha256(changed).hexdigest(), self.rows)
        changed = bytearray(self.image)
        changed[0x003D2BF4 - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "caller consumer/setup drift"):
            verify_callers(bytes(changed), hashlib.sha256(changed).hexdigest())

    def test_caller_evidence_confirms_r0_is_consumed_for_all_four(self):
        evidence = verify_callers(self.image, self.game["code_sha256"])
        self.assertEqual(set(evidence), {hex(address) for address in FUNCTIONS})
        self.assertEqual(evidence["0x14e634"]["instructions"][1]["mnemonic"], "cmp")
        self.assertEqual(evidence["0x3358e0"]["instructions"][-1]["mnemonic"], "beq")
        self.assertIn("not the preceding global/object argument setup",
                      evidence["0x3358e0"]["scope_limit"])
        self.assertEqual(len(CALLER_WINDOWS), 4)


class TestScalarPredicateCases(unittest.TestCase):
    def test_boundaries_and_random_memory_layout(self):
        for address, values in FUNCTIONS.items():
            symbol, size, _instructions, offset, expected, equality, negative = values
            from tools.scalar_predicate_experiment import Spec
            spec = Spec(address, symbol, size, offset, expected, equality, negative)
            cases = list(make_cases(spec, seed=7, samples=16))
            self.assertEqual(len(cases), 24)
            self.assertTrue(any(int.from_bytes(
                case.data[case.registers[0] - DATA + offset:
                          case.registers[0] - DATA + offset + 4], "little") == expected
                for case in cases))
            for case in cases:
                ptr = case.registers[0]
                self.assertGreaterEqual(ptr, DATA)
                self.assertLessEqual(ptr + offset + 4, DATA + DATA_SIZE)
                self.assertEqual(ptr % 4, 0)

    def test_candidates_abi_memory_callers_and_negative_controls(self):
        with tempfile.TemporaryDirectory(prefix="smt4-scalar-predicate-") as temp_dir:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temp_dir),
                          seed=7, samples=32)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["functions"]), 4)
        self.assertEqual(sum(item["cases"] for item in report["functions"]), 160)
        self.assertTrue(all(item["passed"] for item in report["functions"]))
        self.assertEqual(len(report["negative_controls"]), 4)
        self.assertTrue(all(item["detected"] and
                            item["reason"] == "return value differs"
                            for item in report["negative_controls"]))
        self.assertEqual(len(report["caller_windows"]), 8)
        self.assertTrue(all(item["passed"] for item in report["caller_windows"]))


if __name__ == "__main__":
    unittest.main()
