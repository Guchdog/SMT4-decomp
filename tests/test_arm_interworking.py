import struct
import unittest
from tools.arm_interworking import relocate_thumb_call

class InterworkingRelocationTests(unittest.TestCase):
    def test_thumb_blx_encoding_and_alignment(self):
        code = bytearray(struct.pack('<I', 0xebfffffe))
        relocate_thumb_call(code, 0, 0x001ee6e4, 0x002b7f0a, 28, 4)
        self.assertEqual(struct.unpack('<I', code)[0], 0xfb032607)

    def test_tail_veneer_preserves_return_address(self):
        code = bytearray(struct.pack('<I', 0xeafffffe))
        relocate_thumb_call(code, 0, 0x0032c564, 0x002b7f0a, 29, 16)
        self.assertEqual(struct.unpack('<4I', code), (0xeaffffff, 0xe59fc000, 0xe12fff1c, 0x002b7f0b))

    def test_conditional_or_wrong_opcode_rejected(self):
        for word, kind in ((0x1bfffffe,28),(0x1afffffe,29),(0xebfffffe,29),(0xeafffffe,28)):
            with self.subTest(word=hex(word),kind=kind):
                with self.assertRaises(ValueError):
                    relocate_thumb_call(bytearray(struct.pack('<I',word)),0,0x100000,0x2b7f0a,kind,32)

    def test_tail_requires_room(self):
        with self.assertRaises(ValueError):
            relocate_thumb_call(bytearray(struct.pack('<I',0xeafffffe)),0,0x100000,0x2b7f0a,29,12)

    def test_reject_bad_site_or_target(self):
        for site,target in ((0x100002,0x2b7f0a),(0x100000,0x2b7f0b)):
            with self.subTest(site=site,target=target):
                with self.assertRaises(ValueError):
                    relocate_thumb_call(bytearray(struct.pack('<I',0xebfffffe)),0,site,target,28,4)

if __name__ == '__main__':
    unittest.main()
