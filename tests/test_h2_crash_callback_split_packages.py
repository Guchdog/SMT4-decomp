import unittest
from unittest.mock import patch
import tools.h2_crash_callback_split_packages as m
from tools.h2_calc_code_patch import apply_ips
class CallbackSplitTests(unittest.TestCase):
 def setUp(self):
  self.a=bytes(40); b=bytearray(self.a); b[2]=1; b[22]=2; self.b=bytes(b)
  self.r={'calc':[('entry',0x100000,10)],'draw-secondary':[('draw',0x100014,10)]}
 def test_partition_and_orders(self):
  with patch.object(m,'ORIGINAL',m.hash_bytes(self.a)),patch.object(m,'CALLBACK',m.hash_bytes(self.b)):
   images,ips,counts,_=m.split_callback(self.a,self.b,self.r)
   self.assertEqual(counts,{'calc':1,'draw-secondary':1})
   for a,b in [('calc','draw-secondary'),('draw-secondary','calc')]: self.assertEqual(apply_ips(apply_ips(self.a,ips[a]),ips[b]),self.b)
   self.assertEqual(images['calc'][22],0)
 def test_incomplete_partition_fails(self):
  with patch.object(m,'ORIGINAL',m.hash_bytes(self.a)),patch.object(m,'CALLBACK',m.hash_bytes(self.b)):
   with self.assertRaisesRegex(ValueError,'unclassified'): m.split_callback(self.a,self.b,{'calc':self.r['calc'],'draw-secondary':[('draw',0x100014,2)]})
 def test_wrong_source_fails(self):
  with self.assertRaisesRegex(ValueError,'identity'): m.split_callback(self.a,self.b,self.r)
 def test_overlap_fails(self):
  with patch.object(m,'ORIGINAL',m.hash_bytes(self.a)),patch.object(m,'CALLBACK',m.hash_bytes(self.b)):
   with self.assertRaisesRegex(ValueError,'overlapping'): m.split_callback(self.a,self.b,{'calc':[('a',0x100000,25)],'draw-secondary':self.r['draw-secondary']})
if __name__=='__main__': unittest.main()
