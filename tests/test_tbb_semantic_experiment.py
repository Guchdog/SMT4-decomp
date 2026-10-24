import unittest

from tools.semantic_experiment import DATA, DATA_SIZE
from tools.tbb_semantic_experiment import make_row_count_cases, real_tbb_case


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
