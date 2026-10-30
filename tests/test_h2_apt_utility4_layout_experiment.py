import unittest
from tools.h2_apt_utility4_layout_experiment import branch, verify_blob, EXPECTED_BLOB, ADDRESS, CAVE

class LayoutChecks(unittest.TestCase):
    def test_branch_range_and_state(self):
        self.assertEqual(branch(ADDRESS,CAVE).hex(),"d4f704ea")
        with self.assertRaises(ValueError): branch(ADDRESS,CAVE|1)
        with self.assertRaises(ValueError): branch(ADDRESS,ADDRESS+(1<<25)+8)
    def test_exact_body_and_literal_required(self):
        verify_blob(EXPECTED_BLOB,())
        b=bytearray(EXPECTED_BLOB);b[-4]^=1
        with self.assertRaises(ValueError): verify_blob(bytes(b),())
        with self.assertRaises(ValueError): verify_blob(EXPECTED_BLOB,(1,))

if __name__=="__main__": unittest.main()
