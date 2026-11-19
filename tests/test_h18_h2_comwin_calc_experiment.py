import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestH18H2ComWinCalcExperiment(unittest.TestCase):
    def test_callback_states_abi_and_widget_trace(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'run'
            subprocess.run([
                sys.executable,
                str(ROOT / 'tools/h18_h2_comwin_calc_experiment.py'),
                '--output', str(output),
            ], cwd=ROOT, check=True, capture_output=True, text=True)
            report = json.loads((output / 'report.json').read_text())
        self.assertTrue(report['passed'])
        self.assertEqual(report['fixtures'], 27)
        self.assertTrue(report['negative_control']['detected'])
        self.assertFalse(report['overlapping_span']['patched_or_ledger_changed'])
        self.assertEqual(report['literal_table_words']['0x11b0b8'], '0x11b0c8')


if __name__ == '__main__':
    unittest.main()
