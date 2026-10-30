import unittest

from tools.h2_config_mapper_experiment import MAPPERS, expected_index, mapper_access_violation


class ConfigMapperContractTests(unittest.TestCase):
    def test_all_tables_cover_byte_domain_and_fallback(self):
        self.assertEqual(set(MAPPERS), {0x002CAB70, 0x0021F39C, 0x002E0AF4})
        for _address, (_symbol, values) in MAPPERS.items():
            self.assertEqual(len(values), 11)
            self.assertEqual(values, tuple(sorted(values)))
            results = [expected_index(byte, values) for byte in range(256)]
            self.assertEqual(results[0], 0)
            self.assertEqual(results[255], 0)
            for index, boundary in enumerate(values):
                self.assertEqual(expected_index(boundary, values), index)
                if boundary < 255:
                    self.assertEqual(expected_index(boundary + 1, values),
                                     index + 1 if index < 10 else 0)

    def test_wrong_map_fixture_changes_value_eleven(self):
        values = MAPPERS[0x002CAB70][1]
        self.assertEqual(expected_index(11, values), 2)
        wrong_values = (0, 11, *values[2:])
        self.assertEqual(expected_index(11, wrong_values), 1)

    def test_table_read_differences_are_allowed(self):
        original_reads = {0x004077EB, 0x004077EC}
        candidate_reads = set()
        self.assertIsNone(mapper_access_violation(original_reads, candidate_reads,
                                                  set(), set()))

    def test_original_or_candidate_data_stack_write_is_rejected(self):
        write = {0x08001000}
        self.assertEqual(mapper_access_violation(set(), set(), write, set()),
                         {"side": "original", "addresses": ["0x8001000"]})
        self.assertEqual(mapper_access_violation(set(), set(), set(), write),
                         {"side": "candidate", "addresses": ["0x8001000"]})


if __name__ == "__main__":
    unittest.main()
