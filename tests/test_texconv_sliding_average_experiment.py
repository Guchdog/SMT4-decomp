import tempfile
import unittest
from pathlib import Path

from tools.texconv_sliding_average_experiment import (
    FUNCTIONS, ROOT, _case, audit_existing_cpp_source, run, verify_reference,
)


class TestTexConvSlidingAverageExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = __import__("json").loads(
            (ROOT / "config/game_info.json").read_text(encoding="utf-8")
        )
        import csv
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            cls.ledger = list(csv.DictReader(stream))

    def test_existing_helper_is_dormant_and_clone_parameterized(self):
        status = audit_existing_cpp_source()
        self.assertEqual(status["status"], "dormant-static-cpp-draft")
        self.assertEqual(status["maybe_unused_static_definition_count"], 1)
        self.assertFalse(status["production_callsite_found"])
        self.assertEqual({(item["size"], item["stride"]) for item in FUNCTIONS.values()}, {
            (136, 0x400), (136, 0x100), (136, 0x200),
        })

    def test_reference_hash_and_normalized_clone_instructions_are_pinned(self):
        reference = verify_reference(
            self.image, self.game["code_sha256"], self.ledger
        )
        self.assertEqual(set(reference["functions"]), {
            "0x1721e4", "0x1787e4", "0x17ede4",
        })
        self.assertEqual(reference["normalized_instruction_count"], 34)
        self.assertEqual({entry["stride"] for entry in reference["functions"].values()}, {
            "0x400", "0x100", "0x200",
        })

    def test_invalid_zero_count_is_rejected_before_emulation(self):
        with self.assertRaisesRegex(ValueError, "count must be positive"):
            _case(0x001787E4, 0, "invalid-zero-count", 7)

    def test_projected_output_parity_and_controls_fire_but_abi_blocks_full_equivalence(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(
                    ROOT / "extracted/exefs/code.bin", Path(temporary),
                    samples=8, seed=seed,
                )
            self.assertTrue(report["output_parity_passed"], seed)
            self.assertFalse(report["abi_compatible"])
            self.assertFalse(report["full_equivalence_passed"])
            self.assertEqual(report["existing_cpp_source"]["status"],
                             "dormant-static-cpp-draft")
            self.assertEqual(len(report["functions"]), 3)
            for result in report["functions"]:
                self.assertTrue(result["projected_output_memory_passed"], (seed, result))
                self.assertEqual(result["comparisons"], 13)
                self.assertEqual(
                    result["abi_observation"]["original_registers_changed_from_entry"],
                    ["r7", "r9"],
                )
                self.assertEqual(
                    result["abi_observation"]["candidate_registers_changed_from_entry"],
                    [],
                )
            self.assertEqual(len(report["negative_controls"]), 2)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
