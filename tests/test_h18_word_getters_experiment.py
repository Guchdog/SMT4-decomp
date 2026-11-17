import tempfile
import unittest
from pathlib import Path

from tools.h18_word_getters_experiment import ADDRESSES, SEEDS, make_cases, run, verify_reference

ROOT = Path(__file__).resolve().parents[1]

class TestH18WordGettersExperiment(unittest.TestCase):
    def test_originals_are_complete_twelve_byte_word_getters(self):
        report = verify_reference(ROOT / 'extracted/exefs/code.bin')
        self.assertEqual(set(report['functions']), {hex(address) for address in ADDRESSES})
        for address, function in report['functions'].items():
            self.assertEqual(function['size'], 12)
            self.assertEqual(function['instructions'], ['ldr r0, [r0, #4]', 'mov r0, r0', 'bx lr'])
            self.assertEqual(function['original_bytes_hex'], '040090e50000a0e11eff2fe1')

    def test_cases_cover_word_boundaries_and_pointer_edges(self):
        cases = list(make_cases(7, samples=8))
        self.assertEqual(len(cases), 16)
        self.assertEqual(cases[0].registers[0], 0x02000000)
        self.assertEqual(cases[1].registers[0], 0x02000000 + 0x1000 - 8)
        values = [int(case.label.split('-word-')[1].split('-')[0], 16) for case in cases[:8]]
        self.assertEqual(values, [0, 1, 0x7FFFFFFF, 0x80000000,
                                  0xFFFFFFFE, 0xFFFFFFFF, 0x12345678, 0xA5A5A5A5])
        self.assertGreaterEqual(len({case.registers[0] for case in cases}), 3)
        self.assertGreaterEqual(len({case.data for case in cases}), 2)

    def test_two_seed_differentials_and_controls(self):
        for seed in SEEDS:
            with tempfile.TemporaryDirectory() as directory:
                report = run(ROOT / 'extracted/exefs/code.bin', Path(directory), seed=seed, samples=8)
            self.assertTrue(report['passed'], seed)
            self.assertEqual(len(report['functions']), 4)
            self.assertEqual({int(address, 16) for address in report['functions']}, set(ADDRESSES))
            self.assertTrue(all(row['passed'] for row in report['results']))
            self.assertTrue(all(row['candidate_bytes_hex'] == '040090e51eff2fe1'
                                and not row['candidate_bytes_match_original']
                                for row in report['results']))
            self.assertTrue(all(control['detected'] for control in report['negative_controls']))
            self.assertEqual({item['name'] for item in report['negative_controls']},
                             {'negative_wrong_return', 'negative_changed_flags', 'negative_write_memory'})
            self.assertTrue(report['caller_saved_scope_control']['accepted'])

if __name__ == '__main__':
    unittest.main()
