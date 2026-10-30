import unittest
from tools.h2_crash_split_packages import split,hash_bytes
from tools.h2_calc_code_patch import apply_ips
class SplitTest(unittest.TestCase):
 def setUp(self):
  self.a=bytes(32); b=bytearray(self.a); b[1]=5; b[20]=8; self.b=bytes(b)
  self.r={'init-deps':[('a',0x100000,10)],'callbacks':[('b',0x100010,10)]}
 def run_split(self,r=None): return split(self.a,self.b,r or self.r,hash_bytes(self.a),hash_bytes(self.b))
 def test_composition(self):
  images,patches,counts,_=self.run_split(); self.assertEqual(counts,{'init-deps':1,'callbacks':1}); self.assertEqual(apply_ips(apply_ips(self.a,patches['callbacks']),patches['init-deps']),self.b); self.assertEqual(images['callbacks'][1],0)
 def test_unclassified_rejected(self):
  with self.assertRaisesRegex(ValueError,'unclassified'): self.run_split({'init-deps':[('a',0x100000,10)],'callbacks':[('b',0x100010,4)]})
 def test_overlap_rejected(self):
  with self.assertRaisesRegex(ValueError,'overlapping'): self.run_split({'init-deps':[('a',0x100000,20)],'callbacks':[('b',0x100010,10)]})
 def test_wrong_image_rejected(self):
  with self.assertRaisesRegex(ValueError,'identity'): split(self.a,self.b,self.r,'0'*64,hash_bytes(self.b))
if __name__=='__main__': unittest.main()
