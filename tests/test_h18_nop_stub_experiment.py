import tempfile
import unittest
from pathlib import Path

from tools.h18_nop_stub_experiment import ADDRESSES, SEEDS, run
from tools.semantic_experiment_support import load_pinned_reference

ROOT = Path(__file__).resolve().parents[1]

class TestH18NopStubExperiment(unittest.TestCase):
    def test_twenty_one_stubs_pass_two_seed_differentials_and_controls(self):
        for seed in SEEDS:
            with tempfile.TemporaryDirectory() as temp:
                report = run(ROOT / 'extracted/exefs/code.bin', Path(temp), samples=8, seed=seed)
            self.assertTrue(report['passed'], seed)
            self.assertEqual(len(report['functions']), 21)
            self.assertEqual({int(row['address'], 16) for row in report['functions']}, set(ADDRESSES))
            self.assertTrue(all(row['passed'] for row in report['functions']))
            self.assertTrue(all(row['detected'] for row in report['negative_controls']))
            self.assertEqual(report['candidate_bytes_match_claim'], False)
            self.assertFalse(report['whole_function_equivalence_claim'])
            self.assertEqual(report['functional_evidence_level'], 'partial')
            self.assertIn('0x0028ec74', report['first_counterexample']['address'])
            self.assertTrue(all(row['fallthrough_preview'] for row in report['pinned_functions'].values()))

if __name__ == '__main__':
    unittest.main()
