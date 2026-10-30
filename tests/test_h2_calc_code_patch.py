import hashlib
import unittest

from tools.asm_diff import ElfRelocation
from tools.h2_calc_code_patch import (
    apply_ips,
    build_patch,
    normalize_local_text_addends,
    rebase_local_text_relocations,
)
from tools.semantic_experiment import arm_branch


def synthetic_game(image):
    return {
        "code_bin_size": len(image),
        "code_sha256": hashlib.sha256(image).hexdigest(),
        "segments": {
            "text": {
                "vaddr": "0x00100000",
                "size": "0x002FE624",
                "aligned_size": "0x002FF000",
                "file_offset": "0x00000000",
            }
        },
    }


def synthetic_body():
    code = bytearray(16)
    addends = (4, 8, 12, 0)
    relocs = []
    for offset, addend in zip((0, 4, 8, 12), addends):
        code[offset:offset + 4] = addend.to_bytes(4, "little")
        relocs.append(ElfRelocation(offset, 2, "", None))
    return bytes(code), tuple(relocs)


class H2CalcCodePatchTests(unittest.TestCase):
    def test_rebases_only_four_in_body_absolute_references(self):
        code, relocs = synthetic_body()
        fixed, rows = rebase_local_text_relocations(code, relocs, 0x003FE624)
        self.assertEqual(len(rows), 4)
        self.assertEqual(
            [int.from_bytes(fixed[i:i + 4], "little") for i in (0, 4, 8, 12)],
            [0x003FE628, 0x003FE62C, 0x003FE630, 0x003FE624],
        )

    def test_normalizes_translation_unit_relative_relocations(self):
        code = bytearray(128)
        addends = (0x184D0, 0x184E0)
        relocs = tuple(ElfRelocation(offset, 2, "", None) for offset in (60, 64))
        for offset, addend in zip((60, 64), addends):
            code[offset:offset + 4] = addend.to_bytes(4, "little")
        normalized = normalize_local_text_addends(bytes(code), relocs, 0x184C4)
        self.assertEqual(
            [int.from_bytes(normalized[i:i + 4], "little") for i in (60, 64)],
            [0x0C, 0x1C],
        )

    def test_normalization_rejects_references_outside_function(self):
        code = bytearray(32)
        code[0:4] = (0x2050).to_bytes(4, "little")
        reloc = (ElfRelocation(0, 2, "", None),)
        with self.assertRaisesRegex(ValueError, "outside function"):
            normalize_local_text_addends(bytes(code), reloc, 0x2000)

    def test_rejects_unsupported_and_outside_body_relocations(self):
        code, relocs = synthetic_body()
        wrong_type = (ElfRelocation(0, 28, "", None), *relocs[1:])
        with self.assertRaisesRegex(ValueError, "unsupported candidate relocation"):
            rebase_local_text_relocations(code, wrong_type, 0x003FE624)
        bad_code = bytearray(code)
        bad_code[0:4] = (16).to_bytes(4, "little")
        with self.assertRaisesRegex(ValueError, "outside"):
            rebase_local_text_relocations(bytes(bad_code), relocs, 0x003FE624)

    def test_emits_reproducible_patch_and_preserves_other_bytes(self):
        image = bytes(0x00300000)
        code, relocs = synthetic_body()
        patched, ips, manifest = build_patch(image, code, relocs, synthetic_game(image))
        self.assertEqual(apply_ips(image, ips), patched)
        self.assertEqual(manifest["cave_vma"], "0x3fe624")
        self.assertEqual(manifest["branch_target"], "0x3fe624")
        self.assertEqual(manifest["candidate_bytes"], len(code))
        entry_offset = 0x001EA928 - 0x00100000
        cave_offset = 0x002FE624
        allowed = set(range(entry_offset, entry_offset + 4)) | set(range(cave_offset, cave_offset + len(code)))
        changed = {i for i, (before, after) in enumerate(zip(image, patched)) if before != after}
        self.assertTrue(changed <= allowed)
        self.assertEqual(patched[cave_offset:cave_offset + 4], (0x003FE628).to_bytes(4, "little"))

    def test_rejects_wrong_image_hash_and_occupied_cave(self):
        image = bytes(0x00300000)
        code, relocs = synthetic_body()
        game = synthetic_game(image)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            build_patch(image[:-1] + b"\x01", code, relocs, game)
        occupied = bytearray(image)
        occupied[0x002FE624] = 0xFF
        with self.assertRaisesRegex(ValueError, "not all zero"):
            build_patch(bytes(occupied), code, relocs, synthetic_game(bytes(occupied)))

    def test_ips_parser_rejects_truncated_or_out_of_bounds_patch(self):
        with self.assertRaisesRegex(ValueError, "missing EOF"):
            apply_ips(b"\x00\x00", b"PATCH\x00")
        with self.assertRaisesRegex(ValueError, "outside"):
            apply_ips(b"\x00", b"PATCH" + b"\x00\x00\x00\x00\x02abEOF")


if __name__ == "__main__":
    unittest.main()
