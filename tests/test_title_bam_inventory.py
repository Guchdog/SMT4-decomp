import os
import struct
import unittest
from pathlib import Path

from tools.title_bam_inventory import (
    parse_bam_inventory,
    parse_cci_layout,
    parse_cgfx,
    inventory_cci,
)


def _rel32(buffer, pointer_field, target):
    struct.pack_into("<i", buffer, pointer_field, target - pointer_field)


def make_cgfx_fixture(animation_kind=9, animation_name="fixture_anim", frames=24.0):
    """Small CGFX DATA section with one CANM and an empty track dictionary."""
    header_size = 0x14
    data_header_size = 8 + 16 * 8
    data_offset = header_size
    dictionary_offset = data_offset + data_header_size
    dictionary_length = 0x1C + 16  # fixed header/root plus one entry
    dictionary_name_offset = dictionary_offset + dictionary_length
    object_offset = dictionary_name_offset + len(animation_name) + 1
    target_offset = object_offset + 0x28
    animation_end = target_offset + len("fixture_target") + 1
    data_length = animation_end - data_offset
    imag_offset = data_offset + data_length
    imag_length = 8
    file_length = imag_offset + imag_length
    cgfx = bytearray(file_length)

    struct.pack_into("<4sHHIII", cgfx, 0, b"CGFX", 0xFEFF, header_size, 0x05000000, file_length, 2)
    struct.pack_into("<4sI", cgfx, data_offset, b"DATA", data_length)
    pair = data_offset + 8 + animation_kind * 8
    struct.pack_into("<I", cgfx, pair, 1)
    _rel32(cgfx, pair + 4, dictionary_offset)

    struct.pack_into("<4sII", cgfx, dictionary_offset, b"DICT", dictionary_length, 1)
    node = dictionary_offset + 0x1C
    _rel32(cgfx, node + 8, dictionary_name_offset)
    _rel32(cgfx, node + 12, object_offset)
    cgfx[dictionary_name_offset : dictionary_name_offset + len(animation_name)] = animation_name.encode()
    cgfx[dictionary_name_offset + len(animation_name)] = 0

    struct.pack_into("<4sI", cgfx, object_offset, b"CANM", 0x07000001)
    _rel32(cgfx, object_offset + 8, dictionary_name_offset)
    _rel32(cgfx, object_offset + 12, target_offset)
    struct.pack_into("<IfIIi", cgfx, object_offset + 16, 1, frames, 0, 0, 0)
    cgfx[target_offset : target_offset + len("fixture_target")] = b"fixture_target"
    cgfx[target_offset + len("fixture_target")] = 0

    struct.pack_into("<4sI", cgfx, imag_offset, b"IMAG", imag_length)
    return bytes(cgfx)


def make_bam_fixture(cgfx):
    bam = bytearray(0x100 + len(cgfx))
    struct.pack_into("<4sI", bam, 0, b"ATBC", len(bam))
    struct.pack_into("<I", bam, 0x14, 0x80)
    struct.pack_into("<7sxI", bam, 0x80, b"MDLSIGN", len(cgfx))
    bam[0x100:] = cgfx
    return bytes(bam)


class TestCgfxInventorySynthetic(unittest.TestCase):
    def test_reports_animation_name_frames_kind_and_track_count(self):
        parsed = parse_cgfx(make_cgfx_fixture(animation_kind=11, frames=42.5))
        self.assertEqual(parsed["animation_count"], 1)
        self.assertEqual(parsed["track_count"], 0)
        self.assertEqual(
            parsed["animations"],
            [{
                "kind": "visibility",
                "name": "fixture_anim",
                "frames": 42.5,
                "track_count": 0,
            }],
        )

    def test_rejects_bad_sections_and_relative_offsets(self):
        bad_length = bytearray(make_cgfx_fixture())
        struct.pack_into("<I", bad_length, 0x18, 0xFFFFFFFF)
        with self.assertRaisesRegex(ValueError, "section"):
            parse_cgfx(bytes(bad_length))

        bad_pointer = bytearray(make_cgfx_fixture())
        pair = 0x14 + 8 + 9 * 8 + 4
        struct.pack_into("<i", bad_pointer, pair, 0x7FFFFFFF)
        with self.assertRaisesRegex(ValueError, "relative pointer"):
            parse_cgfx(bytes(bad_pointer))

    def test_rejects_malformed_bam_wrapper(self):
        bam = bytearray(make_bam_fixture(make_cgfx_fixture()))
        struct.pack_into("<I", bam, 4, len(bam) - 1)
        with self.assertRaisesRegex(ValueError, "declared size"):
            parse_bam_inventory(bytes(bam), "/fixture.bam")

    def test_validates_ncsd_ncch_ranges(self):
        ncsd = bytearray(0x200)
        ncsd[0x100:0x104] = b"NCSD"
        struct.pack_into("<II", ncsd, 0x120, 2, 20)
        ncch = bytearray(0x200)
        ncch[0x100:0x104] = b"NCCH"
        struct.pack_into("<II", ncch, 0x1B0, 3, 10)
        layout = parse_cci_layout(bytes(ncsd), bytes(ncch), 22 * 0x200)
        self.assertEqual(layout["partition_offset"], 2 * 0x200)
        self.assertEqual(layout["romfs_file_offset"], 5 * 0x200)
        self.assertEqual(layout["romfs_size"], 10 * 0x200)

        with self.assertRaisesRegex(ValueError, "partition"):
            parse_cci_layout(bytes(ncsd), bytes(ncch), 10 * 0x200)


class TestTitleCciIntegration(unittest.TestCase):
    CCI = Path(os.environ.get("SMT4_DECRYPTED_CCI", ""))
    INDEX = Path("extracted/romfs_index.json")

    @unittest.skipUnless(
        str(CCI) and CCI.is_file() and INDEX.is_file(),
        "set SMT4_DECRYPTED_CCI and provide the RomFS index for local CCI integration",
    )
    def test_local_title_bam_animation_inventory(self):
        assets = inventory_cci(self.CCI, self.INDEX)
        self.assertEqual([asset["path"] for asset in assets], ["/title/title_top1.bam", "/title/title_top2.bam"])
        self.assertEqual([asset["animation_count"] for asset in assets], [3, 3])
        self.assertEqual([asset["track_count"] for asset in assets], [50, 43])
        self.assertEqual(
            [[(a["kind"], a["name"], a["frames"], a["track_count"]) for a in asset["animations"]] for asset in assets],
            [
                [("skeletal", "title_top1", 150.0, 18), ("material", "title_top1", 150.0, 14), ("visibility", "title_top1", 150.0, 18)],
                [("skeletal", "title_top2", 1200.0, 11), ("material", "title_top2", 1200.0, 14), ("visibility", "title_top2", 1200.0, 18)],
            ],
        )


if __name__ == "__main__":
    unittest.main()
