import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.state_predicate_experiment import (
    CALLER_WINDOWS, EXPECTED_CALLS, FUNCTIONS, ROOT,
    make_cases, run, verify_callers, verify_reference,
)


class TestStatePredicateReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            import csv
            cls.ledger = list(csv.DictReader(stream))

    def test_reference_hash_and_four_instruction_bodies_are_pinned(self):
        report = verify_reference(self.image, self.game["code_sha256"], self.ledger)
        self.assertEqual(set(report["functions"]), {hex(address) for address in FUNCTIONS})
        self.assertTrue(all(item["size"] == 24 for item in report["functions"].values()))
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, "0" * 64, self.ledger)

    def test_changed_predicate_bytes_fail_closed_even_with_rehashed_image(self):
        changed = bytearray(self.image)
        changed[0x0028C868 - 0x00100000 + 8] ^= 1
        changed = bytes(changed)
        with self.assertRaisesRegex(ValueError, "instructions differ"):
            verify_reference(changed, hashlib.sha256(changed).hexdigest(), self.ledger)

    def test_all_direct_callers_and_tested_windows_are_pinned(self):
        report = verify_callers(self.image, self.ledger)
        self.assertEqual(set(report["all_direct_calls"]), {hex(a) for a in EXPECTED_CALLS})
        self.assertEqual(sum(map(len, report["all_direct_calls"].values())), 19)
        self.assertEqual(len(report["tested_windows"]), 4)
        self.assertEqual(report["tested_windows"]["0x28c868"]["caller"], "btlUI_Calc")


class TestStatePredicateInputs(unittest.TestCase):
    def test_cases_cover_below_equal_above_and_integer_boundaries(self):
        for address, spec in FUNCTIONS.items():
            generated = make_cases(address, seed=7, samples=12)
            labels = {case.label for case in generated}
            self.assertTrue({"below-constant", "equal-constant", "above-constant",
                             "zero", "high-bit", "all-ones"}.issubset(labels))
            self.assertEqual(len(generated), 6 + 12)
            self.assertTrue(all(len(case.data) == 0x1000 for case in generated))
            expected_bias = 0x54A8 if address == 0x0028C868 else 0x2188
            self.assertEqual(spec["caller_r_bias"], expected_bias)


class TestStatePredicateExperiment(unittest.TestCase):
    def test_candidates_offset_constant_sense_controls_and_both_caller_paths(self):
        with tempfile.TemporaryDirectory(prefix="smt4-state-predicate-") as temporary:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                         seed=7, samples=12)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["functions"]), 4)
        self.assertTrue(all(item["passed"] and item["case_count"] == 18
                            for item in report["functions"]))
        self.assertEqual(len(report["negative_controls"]), 12)
        self.assertTrue(all(item["detected"] and item["reason"] == "return value differs"
                            for item in report["negative_controls"]))
        self.assertEqual(len(report["caller_window_results"]), 8)
        self.assertTrue(all(item["passed"] for item in report["caller_window_results"]))
        self.assertTrue(all(not item["writes"] for item in report["caller_window_results"]))
        self.assertEqual({item["path"] for item in report["caller_window_results"]},
                         {"equal", "not-equal"})
        self.assertTrue(report["setup_limitations"])


if __name__ == "__main__":
    unittest.main()
