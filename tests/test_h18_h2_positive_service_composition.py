import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestH18H2PositiveServiceComposition(unittest.TestCase):
    def test_positive_record_reaches_nested_helper_and_matches(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'run'
            subprocess.run([
                sys.executable,
                str(ROOT / 'tools/h18_h2_positive_service_composition.py'),
                '--output', str(output),
            ], cwd=ROOT, check=True, capture_output=True, text=True)
            report = json.loads((output / 'report.json').read_text())
        self.assertTrue(report['passed'])
        self.assertEqual(report['positive_fixture']['record_first_word'], 1)
        for variant in ('original', 'bf_candidate_only', 'nested_candidate_only', 'both_candidates'):
            self.assertEqual(report[variant], report['original'])
        self.assertEqual(report['original']['trace']['nested'], 1)
        self.assertEqual(report['original']['trace']['nested_args'], [0x900100, 1, 0])
        self.assertEqual(report['nonzero_nested_selector']['trace']['nested_args'], [0x900100, 1, 1])
        self.assertTrue(report['negative_control']['detected'])


if __name__ == '__main__':
    unittest.main()
