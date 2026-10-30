import unittest
from tools.h2_manual_comparison_package import compose
from tools.h2_calc_code_patch import apply_ips
class CompositionTest(unittest.TestCase):
    def test_disjoint_and_boundary(self):
        a=bytes(100000); b=bytearray(a); b[1:70000]=b'x'*69999; b[-1]=1
        ips, records=compose(a,bytes(b))
        self.assertEqual(apply_ips(a,ips),bytes(b)); self.assertGreater(len(records),1)
        self.assertNotEqual(apply_ips(a,ips),a)
    def test_reject_size_change(self):
        with self.assertRaises(ValueError): compose(b'a',b'ab')
    def test_eof_offset(self):
        a=bytes(0x454f48); b=bytearray(a); b[0x454f46]=1
        ips,_=compose(a,bytes(b)); self.assertEqual(apply_ips(a,ips),bytes(b))
if __name__=='__main__': unittest.main()
