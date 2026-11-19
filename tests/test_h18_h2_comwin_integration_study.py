import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestH18H2ComWinIntegrationStudy(unittest.TestCase):
    def test_staging_boundaries_and_real_registration_setup(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'run'
            subprocess.run([
                sys.executable,
                str(ROOT / 'tools/h18_h2_comwin_integration_study.py'),
                '--output', str(output),
            ], cwd=ROOT, check=True, capture_output=True, text=True)
            report = json.loads((output / 'report.json').read_text())
            staged = (output / 'staged_code.bin').read_bytes()
            ips = (output / 'candidate.ips').read_bytes()
        self.assertTrue(report['passed'])
        self.assertEqual(report['candidate_bytes'], 144)
        self.assertEqual(report['blx_register_calls'], 3)
        self.assertEqual(report['entry_pointer_bit0'], 0)
        self.assertEqual(report['widget_pointer_bit0'], 0)
        self.assertTrue(report['only_subentry_changed'])
        self.assertTrue(report['ips_roundtrip'])
        registration = report['original_registration_composition']['registration']
        self.assertEqual(registration['name'], 'ComWin Calc')
        self.assertEqual(registration['callback_ptr'], 0x0011B094)
        self.assertEqual(report['original_registration_composition'], report['staged_registration_composition'])
        self.assertGreater(len(staged), len(ips))


if __name__ == '__main__':
    unittest.main()
