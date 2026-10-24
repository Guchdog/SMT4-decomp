import json
import unittest
from pathlib import Path

from tools.eff_polygon_thunder_prefix_experiment import ROOT, run


class TestEffPolygonThunderPrefixExperiment(unittest.TestCase):
    def test_three_point_count_prefixes_match_cpp_candidates(self):
        output = ROOT / "build/semantic-equivalence/eff-polygon-thunder-prefix"
        report = run(ROOT / "extracted/exefs/code.bin", output,
                     samples=128, seed=20261024)
        self.assertTrue(report["passed"], json.dumps(report, indent=2))
        self.assertEqual(len(report["results"]), 3)
        self.assertEqual(len(report["negative_controls"]), 3)
        self.assertTrue(all(row["cases"] >= 600 for row in report["results"]))
        self.assertTrue(all(row["detected"] for row in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
