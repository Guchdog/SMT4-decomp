import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.null_chain_experiment import (
    FUNCTIONS, ROOT, make_cases, run, verify_reference,
)
from tools.semantic_experiment import DATA, DATA_SIZE


class TestNullChainReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))

    def test_all_five_bodies_match_pinned_instructions(self):
        result = verify_reference(self.image, self.game["code_sha256"])
        self.assertEqual(set(result["functions"]), {hex(address) for address in FUNCTIONS})
        self.assertTrue(all(item["size"] == 16 for item in result["functions"].values()))
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, "0" * 64)

    def test_reference_bytes_reject_drift_even_with_recomputed_image_hash(self):
        changed = bytearray(self.image)
        changed[0x003DF588 - 0x00100000] ^= 1
        changed = bytes(changed)
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            verify_reference(changed, hashlib.sha256(changed).hexdigest())


class TestNullChainInputs(unittest.TestCase):
    def test_cases_cover_null_links_valid_paths_and_last_mapped_word(self):
        for address in FUNCTIONS:
            generated = make_cases(address, seed=7, samples=12)
            labels = {case.label for case in generated}
            self.assertTrue({"valid-chain", "null-intermediate", "null-leaf-result",
                             "root-field-last-word", "leaf-field-last-word"}.issubset(labels))
            self.assertEqual(len(generated), 7 + 12)
            for case in generated:
                self.assertEqual(len(case.data), DATA_SIZE)
                self.assertGreaterEqual(case.registers[0], DATA)
                self.assertLess(case.registers[0], DATA + DATA_SIZE)


class TestNullChainExperiment(unittest.TestCase):
    def test_candidates_footprints_negative_offsets_and_null_base(self):
        with tempfile.TemporaryDirectory(prefix="smt4-null-chain-") as temp_dir:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temp_dir),
                         seed=7, samples=12)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["candidate_functions"]), 5)
        self.assertTrue(all(item["passed"] and item["case_count"] == 19
                            for item in report["candidate_functions"]))
        self.assertEqual(len(report["negative_controls"]), 10)
        self.assertTrue(all(item["detected"] and item["reason"] == "return value differs"
                            for item in report["negative_controls"]))
        self.assertTrue(all(item["both_faulted"]
                            for item in report["null_base_behavior"].values()))
        self.assertFalse(report["caller_window"]["added"])
        self.assertTrue(all(not sites for sites in
                            report["caller_window"]["direct_bl_references"].values()))


if __name__ == "__main__":
    unittest.main()
