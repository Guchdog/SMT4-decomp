from __future__ import annotations

import random
import unittest

from tools.h2_copy_pair_production_experiment import (
    directed_cases, H2_CONFIG, ERROR_STRING, BASE,
)


class H2CopyPairProductionTests(unittest.TestCase):
    def test_directed_matrix_covers_alignment_overlap_and_real_sources(self):
        cases = list(directed_cases(random.Random(7)))
        labels = {case.label for case in cases}
        self.assertEqual(len(cases), 33)
        for destination_offset in range(4):
            for source_offset in range(4):
                self.assertIn(
                    f"alignment-dst-{destination_offset}-src-{source_offset}",
                    labels,
                )
        for delta in range(-7, 8):
            self.assertIn(f"overlap-byte-delta-{delta:+d}", labels)
        self.assertIn("h2-config-global-source", labels)
        self.assertIn("readonly-odd-error-string", labels)
        h2_case = next(case for case in cases if case.label == "h2-config-global-source")
        error_case = next(case for case in cases if case.label == "readonly-odd-error-string")
        self.assertEqual(h2_case.registers[1], H2_CONFIG)
        self.assertEqual(error_case.registers[1], ERROR_STRING)
        self.assertEqual(error_case.registers[0] % 4, 0)

    def test_overlap_cases_share_the_same_data_arena(self):
        cases = list(directed_cases(random.Random(9)))
        overlap = [case for case in cases if case.label.startswith("overlap-byte-delta-")]
        self.assertEqual(len(overlap), 15)
        self.assertTrue(all(case.registers[0] >= BASE and case.registers[1] >= BASE
                            for case in overlap))


if __name__ == "__main__":
    unittest.main()
