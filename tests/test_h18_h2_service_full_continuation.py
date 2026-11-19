import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestH18H2ServiceFullContinuation(unittest.TestCase):
    def test_service_reaches_return_across_later_record_branches(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'run'
            subprocess.run([
                sys.executable,
                str(ROOT / 'tools/h18_h2_service_full_continuation.py'),
                '--output', str(output),
            ], cwd=ROOT, check=True, capture_output=True, text=True)
            report = json.loads((output / 'report.json').read_text())
        self.assertTrue(report['passed'])
        for scenario, variants in report['results'].items():
            original = variants['original']
            self.assertTrue(original['trace']['returned'], scenario)
            self.assertTrue(original['callee_saved_restored'], scenario)
            for key in ('bf_candidate_only', 'nested_candidate_only', 'both_candidates'):
                self.assertEqual(variants[key], original, f'{scenario}/{key}')
        trace = report['results']['all_positive']['original']['trace']
        self.assertEqual((trace['field_a'], trace['field_b'], trace['field_c']), (1, 1, 1))
        self.assertTrue(report['negative_control']['detected'])


if __name__ == '__main__':
    unittest.main()
