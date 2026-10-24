import unittest
import hashlib
import json

from tools.semantic_experiment import DATA, DATA_SIZE
from tools.tbb_semantic_experiment import (
    ROOT, make_row_count_cases, real_tbb_case, title_menu_case,
    verify_title_call_sites,
)


class TestRealTbbCases(unittest.TestCase):
    def test_places_real_container_and_arguments_in_oracle_state(self):
        raw = b"TBCR" + bytes(range(28))
        case = real_tbb_case(raw, "real", table_index=3, seed=9)

        self.assertEqual(case.registers[0], DATA + 0x100)
        self.assertEqual(case.registers[1], 3)
        self.assertEqual(case.data[0x100 : 0x100 + len(raw)], raw)
        self.assertEqual(len(case.data), DATA_SIZE)

    def test_payload_case_points_directly_at_real_subtable(self):
        raw = b"TBCR" + bytes(range(28))
        table_pointer = DATA + 0x158
        case = real_tbb_case(raw, "payload", table_pointer=table_pointer, seed=10)

        self.assertEqual(case.registers[0], table_pointer)
        self.assertEqual(case.data[0x100 : 0x100 + len(raw)], raw)

    def test_rejects_asset_larger_than_mapped_region(self):
        with self.assertRaisesRegex(ValueError, "does not fit"):
            real_tbb_case(bytes(DATA_SIZE), "too-large")


class TestTitleCallerWindowSetup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        cls.reference_hash = game["code_sha256"]

    def test_title_window_call_sites_match_the_pinned_reference(self):
        sites = verify_title_call_sites(self.image, self.reference_hash)
        self.assertEqual(sites["0x1e9ab8"]["operands"], "#0x2c0ec4")
        self.assertEqual(sites["0x1e9ac4"]["operands"], "#0x2c0e9c")
        self.assertEqual(sites["0x2c0ed8"]["operands"], "#0x2ac2f4")

    def test_title_window_fails_closed_on_hash_or_callsite_drift(self):
        with self.assertRaisesRegex(ValueError, "hash"):
            verify_title_call_sites(self.image, "0" * 64)
        changed = bytearray(self.image)
        changed[0x001E9AB8 - 0x00100000] ^= 1
        changed = bytes(changed)
        with self.assertRaisesRegex(ValueError, "callsite mismatch"):
            verify_title_call_sites(changed, hashlib.sha256(changed).hexdigest())

    def test_title_menu_cases_set_only_the_valid_selection_register(self):
        raw = b"TBCR" + bytes(range(28))
        for selection in range(4):
            case = title_menu_case(selection, raw, seed=3)
            self.assertEqual(case.registers[6], selection)
            self.assertEqual(case.data[0x100:0x100 + len(raw)], raw)
        with self.assertRaisesRegex(ValueError, "0..3"):
            title_menu_case(4, raw)

    def test_row_count_generator_covers_division_edges_and_is_reproducible(self):
        cases = list(make_row_count_cases(7, 4))
        self.assertEqual(len(cases), 12)
        self.assertEqual(
            [case.label for case in cases[:8]],
            ["null", "wrong-magic", "zero-stride", "zero-payload",
             "payload-below-stride", "exact-divisibility",
             "truncated-division", "large-u32-values"],
        )
        again = list(make_row_count_cases(7, 4))
        self.assertEqual(cases, again)


if __name__ == "__main__":
    unittest.main()
