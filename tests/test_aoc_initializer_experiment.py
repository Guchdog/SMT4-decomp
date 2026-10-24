import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.aoc_initializer_experiment import (
    FUNCTIONS, ROOT, make_cases, run, verify_callers, verify_reference,
)
from tools.semantic_experiment import DATA, DATA_SIZE


class TestAocInitializerReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        cls.reference_hash = cls.game["code_sha256"]

    def test_all_three_reference_bodies_match_the_pinned_four_word_pattern(self):
        result = verify_reference(self.image, self.reference_hash)
        self.assertEqual(set(result["functions"]), {hex(addr) for addr in FUNCTIONS})
        self.assertTrue(all(item["size"] == 36 for item in result["functions"].values()))
        self.assertEqual(len({item["sha256"] for item in result["functions"].values()}), 1)

    def test_caller_bounds_and_argument_layouts_are_pinned(self):
        evidence = verify_callers(self.image, self.reference_hash)
        self.assertEqual(len(evidence["aoc_texture"]), 5)
        self.assertEqual(evidence["aoc_texture"][3]["operands"], "#0x3530f8")
        self.assertEqual(evidence["aoc_archive"][3]["operands"], "#0x352950")
        self.assertEqual(evidence["script_vm_descriptor"][5]["operands"], "#0x354d28")
        self.assertEqual(evidence["script_vm_descriptor"][-1]["operands"], "#0x354c30")

    def test_reference_and_callers_fail_closed_on_drift(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, "0" * 64)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_callers(self.image, "0" * 64)

        changed = bytearray(self.image)
        changed[0x0038DEBC - 0x00100000] ^= 1
        changed = bytes(changed)
        changed_hash = hashlib.sha256(changed).hexdigest()
        with self.assertRaisesRegex(ValueError, "caller bounds/type evidence drift"):
            verify_callers(changed, changed_hash)

        changed = bytearray(self.image)
        changed[0x003530F8 - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "initializer bytes differ"):
            verify_reference(bytes(changed), hashlib.sha256(changed).hexdigest())


class TestAocInitializerExperiment(unittest.TestCase):
    def test_case_generator_covers_callers_aliases_boundaries_and_stays_in_ram(self):
        generated = list(make_cases(0x00352950, seed=7, samples=32))
        labels = {case.label for case in generated}
        self.assertTrue({"aoc-texture-caller", "aoc-archive-caller",
                         "script-vm-caller", "source-buffer-same",
                         "source-points-at-object", "boundary-zero-size"}.issubset(labels))
        self.assertEqual(len(generated), 12 + 32)
        for case in generated:
            object_pointer = case.registers[0]
            self.assertEqual(object_pointer % 4, 0)
            self.assertGreaterEqual(object_pointer, DATA)
            self.assertLessEqual(object_pointer + 0x10, DATA + DATA_SIZE)
            self.assertEqual(len(case.data), DATA_SIZE)

    def test_differential_candidates_pass_and_negative_control_is_detected(self):
        with tempfile.TemporaryDirectory(prefix="smt4-aoc-init-") as temp_dir:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temp_dir),
                         seed=7, samples=16)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["candidate_functions"]), 3)
        self.assertTrue(all(item["passed"] for item in report["candidate_functions"]))
        self.assertTrue(all(item["case_count"] == 28
                            for item in report["candidate_functions"]))
        self.assertEqual(len(report["negative_controls"]), 3)
        self.assertTrue(all(item["detected"] and
                            item["reason"] == "data memory differs"
                            for item in report["negative_controls"]))
        self.assertTrue(all(not item["byte_identical"]
                            for item in report["candidate_functions"]))


if __name__ == "__main__":
    unittest.main()
