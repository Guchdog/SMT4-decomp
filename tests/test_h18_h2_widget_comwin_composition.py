import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = (
    'original+original',
    'original+widget_candidate',
    'comwin_candidate+original',
    'comwin_candidate+widget_candidate',
)


class TestH18H2WidgetComWinComposition(unittest.TestCase):
    def test_widget_and_comwin_four_way_composition(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'run'
            subprocess.run([
                sys.executable,
                str(ROOT / 'tools/h18_h2_widget_comwin_composition.py'),
                '--output', str(output),
            ], cwd=ROOT, check=True, capture_output=True, text=True)
            report = json.loads((output / 'report.json').read_text())
        self.assertTrue(report['passed'])
        self.assertEqual(len(report['cases']), 13)
        for name, case in report['cases'].items():
            original = case['variants']['original+original']
            for variant in VARIANTS:
                self.assertEqual(case['variants'][variant], original, f'{name}/{variant}')
        interpolation = report['cases']['state1_interpolation']['variants']['original+original']['helper_trace']
        self.assertEqual([event[0] for event in interpolation], [2, 2, 3, 4, 5])
        animation = report['cases']['state1_animation_sequence']['variants']['original+original']['helper_trace']
        self.assertEqual([event[0] for event in animation], [1, 3, 4, 5])
        for control in report['negative_controls'].values():
            self.assertTrue(control['detected'])


if __name__ == '__main__':
    unittest.main()
