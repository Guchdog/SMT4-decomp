from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "experiments/semantic_equivalence/h18_003f32f4_family.cpp"
RUNNER = ROOT / "tools/h18_003f32f4_family.py"

from tools.h18_003f32f4_family import ENTRIES, EXTENT, expected_words, original_entry


class InitializerFamilyTests(unittest.TestCase):
    def test_editable_candidate_and_differential_runner_exist(self) -> None:
        self.assertTrue(CPP.is_file(), "missing editable initializer family")
        self.assertTrue(RUNNER.is_file(), "missing per-entry differential runner")

    def test_all_eight_entry_boundaries_and_literal_pools(self) -> None:
        image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        addresses = [entry["address"] for entry in ENTRIES]
        self.assertEqual(addresses, [0x003F32F4, 0x003F3320, 0x003F334C, 0x003F3378,
                                     0x003F33A4, 0x003F33D0, 0x003F33FC, 0x003F3428])
        for entry in ENTRIES:
            with self.subTest(address=hex(entry["address"])):
                self.assertEqual(len(original_entry(image, entry)), EXTENT)
                self.assertEqual(len(expected_words(entry)), 4)
        # These two routines intentionally use the base literal + 8 for the -1 pair.
        self.assertEqual(ENTRIES[1]["pair_offset"], 8)
        self.assertEqual(expected_words(ENTRIES[1])[0x00433E20], 0xFFFFFFFF)
        self.assertEqual(expected_words(ENTRIES[7])[0x0044E5A0], 0xFFFFFFFF)


if __name__ == "__main__":
    unittest.main()
