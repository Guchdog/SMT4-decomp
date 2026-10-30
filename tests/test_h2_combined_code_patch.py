import struct
import unittest

from tools.h2_combined_code_patch import (
    SECONDARY_CAVE_VMA,
    SECONDARY_VMA,
    align_up,
    arm_branch_target,
    parse_elf32,
    patch_call,
)
from tools.semantic_experiment import arm_branch


class H2CombinedCodePatchTests(unittest.TestCase):
    def test_arm_call_relocation_encodes_final_target_and_preserves_condition(self):
        place = 0x002CAFD0 + 332
        target = 0x003FEE54
        original = 0x1BFFFFFE  # conditional BL with an unresolved REL addend
        patched = patch_call(original, place, target)
        self.assertEqual(patched & 0xFF000000, 0x1B000000)
        displacement = (patched & 0xFFFFFF) << 2
        if displacement & 0x02000000:
            displacement -= 0x04000000
        self.assertEqual(place + 8 + displacement, target)

    def test_arm_call_rejects_non_bl_and_unreachable_targets(self):
        with self.assertRaisesRegex(ValueError, "not ARM BL"):
            patch_call(0xEA000000, 0x1000, 0x2000)
        with self.assertRaisesRegex(ValueError, "out of range"):
            patch_call(0xEB000000, 0x1000, 0x10000000)

    def test_alignment_and_elf_header_are_checked(self):
        self.assertEqual(align_up(127, 4), 128)
        with self.assertRaisesRegex(ValueError, "ELF32"):
            parse_elf32(__import__("pathlib").Path(__file__))

    def test_secondary_entry_branch_reaches_its_final_cave_vma(self):
        branch = struct.unpack("<I", arm_branch(SECONDARY_VMA, SECONDARY_CAVE_VMA))[0]
        self.assertEqual(arm_branch_target(branch, SECONDARY_VMA), SECONDARY_CAVE_VMA)


if __name__ == "__main__":
    unittest.main()
