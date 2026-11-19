import tempfile
import unittest
from pathlib import Path
from tools.h18_003f3454_family import ENTRIES, ROOT, run

class TestH18003f3454Family(unittest.TestCase):
    def test_three_initializer_entries_and_tail_model(self):
        with tempfile.TemporaryDirectory() as temp:
            report=run(ROOT/"extracted/exefs/code.bin",Path(temp),seed=19,samples=4)
        self.assertTrue(report["passed"])
        self.assertEqual(set(report["entries"]),{hex(a) for a in ENTRIES})
        self.assertTrue(all(x["passed"] for x in report["entries"].values()))
        self.assertTrue(all(x["detected"] for x in report["negative_controls"]))
        self.assertEqual(report["boundaries"]["0x3f3454"]["pool_words"],
                         ["0x471a38","0x471a48","0x353120","0x4e62c0"])
        self.assertEqual(report["boundaries"]["0x3f34a0"]["pool_words"],
                         ["0x472570","0x472578"])
        self.assertEqual(report["boundaries"]["0x3f34cc"]["pool_words"],
                         ["0x472798","0x4727a0"])
        tail=report["entries"][hex(0x003F3454)]["results"][0]["helper_trace"]
        self.assertEqual(tail[0]["helper"],"vector_constructor_iterator")
        self.assertTrue(tail[0]["thumb_state"])
        self.assertEqual(tail[0]["count"],0x40)
        self.assertEqual(tail[0]["stride"],8)
        self.assertEqual(tail[0]["modeled_callbacks"],0x40)
        self.assertEqual(tail[0]["constructor_pointer_state"],"ARM")

if __name__=="__main__": unittest.main()
