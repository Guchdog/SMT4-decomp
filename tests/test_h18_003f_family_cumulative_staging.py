import unittest
from pathlib import Path
from tools.h2_calc_code_patch import encode_ips
from tools.h18_003f_family_cumulative_staging import (ROOT,IMAGE_BASE,SLOTS,ADDRS,compose_images,decode_ips_records)

class CumulativeStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.original=(ROOT/'extracted/exefs/code.bin').read_bytes()
    def candidate_map(self): return {a:bytes([i+1])*16 for i,(a,_n,_name) in enumerate(SLOTS)}
    def test_compose_roundtrips_and_preserves_h2_cave_and_3454(self):
        original=self.original; empty_ips=b'PATCHEOF'; candidates=self.candidate_map()
        result=compose_images(original,original,empty_ips,candidates)
        cave_off=0x003FE624-IMAGE_BASE; cave_end=0x003FF000-IMAGE_BASE
        self.assertEqual(result['image'][cave_off:cave_end],original[cave_off:cave_end])
        self.assertTrue(result['cave_unchanged']); self.assertTrue(result['3454_unchanged'])
        self.assertTrue(result['ips_roundtrip'])
        self.assertEqual(len(result['placements']),11)
    def test_rejects_base_bytes_changed_in_target_slot(self):
        original=self.original; candidates=self.candidate_map(); base=bytearray(original)
        off=SLOTS[0][0]-IMAGE_BASE; base[off]^=1
        ips=encode_ips([(off,bytes([base[off]]))],len(base))
        with self.assertRaisesRegex(ValueError,'slot .* not byte-identical'):
            compose_images(original,bytes(base),ips,candidates)
    def test_rejects_h18_ips_record_overlapping_even_unchanged_slot(self):
        original=self.original; candidates=self.candidate_map(); off=SLOTS[0][0]-IMAGE_BASE
        ips=encode_ips([(off,original[off:off+4])],len(original))
        with self.assertRaisesRegex(ValueError,'IPS record overlaps target slot'):
            compose_images(original,original,ips,candidates)
    def test_rejects_candidate_overflow_and_extra_entry(self):
        original=self.original; c=self.candidate_map(); c[SLOTS[0][0]]=bytes(SLOTS[0][1]+4)
        with self.assertRaisesRegex(ValueError,'exceeds slot'):
            compose_images(original,original,b'PATCHEOF',c)
        c=self.candidate_map(); c[0x003F3454]=bytes(4)
        with self.assertRaisesRegex(ValueError,'exactly'):
            compose_images(original,original,b'PATCHEOF',c)

if __name__=='__main__': unittest.main()
