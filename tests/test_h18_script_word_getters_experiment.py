import tempfile
import unittest
from pathlib import Path

from tools.h18_script_word_getters_experiment import (
    ADDRESSES, CALLER_WINDOWS, HALFWORDS, SEEDS, make_cases, run, verify_reference,
)

ROOT = Path(__file__).resolve().parents[1]

class TestH18ScriptWordGetters(unittest.TestCase):
    def test_pinned_entries_and_sixteen_direct_callers_each(self):
        ref = verify_reference(ROOT / 'extracted/exefs/code.bin')
        self.assertEqual(set(ref['functions']), {hex(address) for address in ADDRESSES})
        self.assertEqual(ref['functions']['0x2345f0']['original_bytes_hex'], 'b804d0e1ff0000e21eff2fe1')
        self.assertEqual(ref['functions']['0x2345fc']['original_bytes_hex'], 'ba04d0e1ff0000e21eff2fe1')
        self.assertTrue(all(len(ref['direct_callers'][hex(address)]) == 16 for address in ADDRESSES))
        self.assertEqual({site['caller'] for site in ref['direct_callers']['0x2345f0']},
                         {'script_vm_func_0038c43c','script_vm_func_0038cdf4',
                          'script_vm_func_0038d7b0','script_vm_func_0038de60'})

    def test_case_boundaries_are_unsigned_low_bytes_and_aligned(self):
        for address in ADDRESSES:
            cases = list(make_cases(address, seed=7, samples=4))
            self.assertEqual(len(cases), len(HALFWORDS) + 4)
            for case in cases:
                self.assertEqual(case.registers[0] & 3, 0)
                offset = 0x48 if address == ADDRESSES[0] else 0x4A
                raw = int.from_bytes(case.data[case.registers[0] - 0x02000000 + offset:
                                                  case.registers[0] - 0x02000000 + offset + 2], 'little')
                self.assertEqual(raw & 0xFF, int(case.label.split('-result-')[1], 16))

    def test_two_seed_differentials_controls_and_real_caller_pair_windows(self):
        for seed in SEEDS:
            with tempfile.TemporaryDirectory() as temp:
                report = run(ROOT / 'extracted/exefs/code.bin', Path(temp), seed=seed, samples=8)
            self.assertTrue(report['passed'], seed)
            self.assertEqual(len(report['results']), 2)
            self.assertTrue(all(result['passed'] for result in report['results']))
            self.assertTrue(all(control['detected'] for control in report['negative_controls']))
            self.assertEqual({control['name'] for control in report['negative_controls']},
                             {'wrong_offset','signed_extension','omitted_mask','memory_write'})
            self.assertTrue(all(window['passed'] for window in report['caller_windows']))
            self.assertEqual({window['target'] for window in report['caller_windows']},
                             {'0x002345f0','0x002345fc'})

if __name__ == '__main__':
    unittest.main()
