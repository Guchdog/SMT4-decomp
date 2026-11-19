from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "experiments/semantic_equivalence/h18_003f3274_candidate.cpp"
RUNNER = ROOT / "tools/h18_003f3274_experiment.py"

from tools.h18_003f3274_experiment import EXPECTED_STORES, original_function


class Function003F3274ContractTests(unittest.TestCase):
    def test_editable_candidate_and_differential_runner_exist(self) -> None:
        self.assertTrue(CANDIDATE.is_file(), "missing editable C++ candidate")
        self.assertTrue(RUNNER.is_file(), "missing private differential runner")

    def test_initialization_constants_are_explicit(self) -> None:
        source = CANDIDATE.read_text(encoding="utf-8")
        for expected in ("0x00465080u", "0x00465088u", "0x004E39E0u", "0x00100000u", "0x00080000u", "0x00008058u"):
            with self.subTest(expected=expected):
                self.assertIn(expected.lower(), source.lower())

    def test_original_entry_boundary_and_literal_pool(self) -> None:
        image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        body = original_function(image)
        self.assertEqual(len(body), 0x80)
        self.assertEqual(len(EXPECTED_STORES), 15)
        self.assertEqual(EXPECTED_STORES[0x004E3BDC], 0x00008051)


if __name__ == "__main__":
    unittest.main()
