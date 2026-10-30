import unittest
from tools.h2_apt_utility4_caller_composition import BL,B,FALL,expected_site_bytes
from tools.h2_apt_utility4_layout_experiment import branch
from tools.h2_apt_utility4_entry_experiment import ADDRESS

class CallerSiteTests(unittest.TestCase):
    def test_bl_and_tail_are_distinct(self):
        for site in BL:self.assertEqual(expected_site_bytes(site),branch(site,ADDRESS,True))
        for site in B:self.assertEqual(expected_site_bytes(site),branch(site,ADDRESS,False))
        self.assertIsNone(expected_site_bytes(FALL))

if __name__=="__main__":unittest.main()
