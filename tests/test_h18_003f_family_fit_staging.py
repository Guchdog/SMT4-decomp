import unittest
from tools.h18_003f_family_fit_staging import SLOTS,EXPECTED_ADDRS,stage_candidates,validate_patch_scope

class FamilyFitStagingTests(unittest.TestCase):
    def test_exact_eleven_slots_stage_and_roundtrip_without_3454(self):
        image=bytes([0xA5])*0x00400000
        candidates={addr:bytes([i+1])*min(16,extent) for i,(addr,extent,_name) in enumerate(SLOTS)}
        staged,ips,rows=stage_candidates(image,candidates)
        self.assertEqual(len(rows),11)
        scope=validate_patch_scope(image,staged,ips,candidates)
        self.assertTrue(scope['ips_roundtrip'])
        self.assertTrue(scope['oversized_003f3454_unchanged'])
        self.assertEqual(staged[0x003F3454-0x00100000:0x003F34A0-0x00100000],image[0x003F3454-0x00100000:0x003F34A0-0x00100000])

    def test_oversized_or_extra_entry_is_rejected(self):
        image=bytes([0])*0x00400000
        candidates={addr:bytes([0x11])*min(16,extent) for addr,extent,_ in SLOTS}
        candidates[0x003F3274]=bytes(0x84)
        with self.assertRaisesRegex(ValueError,'exceed'):
            stage_candidates(image,candidates)
        candidates[0x003F3274]=bytes(16)
        candidates[0x003F3454]=bytes(4)
        with self.assertRaisesRegex(ValueError,'exactly'):
            stage_candidates(image,candidates)

if __name__=='__main__': unittest.main()

